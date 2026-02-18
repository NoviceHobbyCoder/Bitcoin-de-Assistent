import json
from queue import Queue, Empty
import socketio
import threading
import time

class WebSocketClient:
    def __init__(self, callback, logger, db_handler):
        self.callback = callback
        self.logger = logger
        self.db_handler = db_handler
        self.connected = False
        self.running = False
        self.db_queue = Queue()

        # Initialize Socket.IO client
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,    
            reconnection_attempts=None,   # Unbegrenzte Wiederverbindungsversuche
            reconnection_delay=1
        )

        # Register event handlers
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('add_order', self._on_add_order, namespace='/market')
        self.sio.on('remove_order', self._on_remove_order, namespace='/market')
        
    def _start_db_worker(self, num_workers=4):
        """Start multiple database worker threads"""
        def db_worker():
            self.logger.info("Database worker thread started")
            while self.running:
                try:
                    # Get order from queue with timeout
                    order_data = self.db_queue.get(timeout=1)
                    
                    # Process the order
                    action = order_data.get('action')
                    order = order_data.get('order')
                    
                    if action == 'add':
                        self.db_handler._add_order(order)
                    elif action == 'remove':
                        self.db_handler._remove_order(order)
                    
                    # Mark task as done
                    self.db_queue.task_done()
                    self.logger.debug(f"Processed {action} order: {order.get('order_id')}")
                    
                except Empty:
                    # Timeout, just continue
                    pass
                except Exception as e:
                    self.logger.error(f"Error in db_worker: {str(e)}")
                    self.logger.exception("Full traceback:")
        
        # Start multiple threads
        for i in range(num_workers):
            thread = threading.Thread(target=db_worker, daemon=True, name=f"DBWorker-{i}")
            thread.start()
        self.logger.info(f"Started {num_workers} database worker threads")
    
        # Starte mehrere Threads
        for _ in range(num_workers):
            threading.Thread(target=db_worker, daemon=True).start()
        self.logger.info(f"Started {num_workers} database worker threads")
           
    def connect(self):
        """Start WebSocket connection"""
        if not self.running:
            self.logger.info("Starting WebSocket client...")
            self.running = True
            self._start_db_worker()  # Start database worker first
            self.ws_thread = threading.Thread(target=self._connect_ws)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            self.logger.info("WebSocket client started")
        elif not self.connected:
            self.logger.info("Reconnecting WebSocket client...")
            self.ws_thread = threading.Thread(target=self._connect_ws)
            self.ws_thread.daemon = True
            self.ws_thread.start()
        
    def _connect_ws(self):
        """WebSocket connection handler"""
        try:
            self.logger.debug("Connecting to WebSocket...")
            self.sio.connect(
                'https://ws.bitcoin.de:443',
                namespaces=['/market']
            )
            
            # Keep the connection alive
            while self.running and self.sio.connected:
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {str(e)}")
            self.connected = False
        finally:
            if self.sio.connected:
                self.sio.disconnect()

    def _on_connect(self):
        """Handle Socket.IO connection"""
        try:
            self.connected = True
            self.logger.info("WebSocket connected")
            # Join the market namespace
            self.sio.emit('join', namespace='/market')
            self.logger.debug("Joined market namespace")
        except Exception as e:
            self.logger.error(f"Error in connect handler: {str(e)}")

    def _on_disconnect(self):
        """Handle Socket.IO disconnection"""
        self.connected = False
        self.logger.info("WebSocket disconnected")
        if self.running:
            self.logger.info("Attempting to reconnect...")
            self.connect()  # Attempt to reconnect

    def _on_add_order(self, order):
        """Handle add_order event"""
        try:
            self.logger.info(f"WebSocket received add_order: {order.get('order_id', 'unknown')}")
        
            # Transform the data into a standardized format
            processed_order = {
                'id': order.get('id'),
                'order_id': order.get('order_id'),
                'order_type': order.get('order_type'),
                'trading_pair': order.get('trading_pair'),
                'price': float(order.get('price', 0)),
                'amount': float(order.get('amount', 0)),
                'min_amount': float(order.get('min_amount', 0)),
                'volume': float(order.get('volume', 0)),
                'seat_of_bank': order.get('seat_of_bank_of_creator'),
                'min_trust_level': order.get('min_trust_level'),
                'trade_to_sepa_country': order.get('trade_to_sepa_country'),
                'is_kyc_full': bool(int(order.get('is_kyc_full', 0))),
                'payment_option': int(order.get('payment_option', 0)),
                'raw_data': json.dumps(order)
            }
        
            # Queue database operation FIRST (before callback!)
            self.db_queue.put({
                'action': 'add',
                'order': processed_order
            })
            self.logger.info(f"Queued add_order to database: {processed_order['order_id']}")
            
            # Call callback for GUI update AFTER queueing
            if self.callback:
                self.callback({
                    'action': 'add',
                    'order': processed_order
                })
                self.logger.debug(f"GUI callback triggered for add_order: {processed_order['order_id']}")
        
        except Exception as e:
            self.logger.error(f"Error in _on_add_order: {str(e)}")
            self.logger.exception("Full traceback:")
              
    def _on_remove_order(self, order):
        """Handle remove_order event"""
        try:
            order_id = order.get('order_id', 'unknown')
            self.logger.info(f"WebSocket received remove_order: {order_id}")
            
            # Transform the data into a standardized format
            processed_order = {
                'id': order.get('id'),
                'order_id': order.get('order_id'),
                'order_type': order.get('order_type'),
                'trading_pair': order.get('trading_pair'),
                'raw_data': json.dumps(order)
            }
            
            # Queue database operation FIRST
            self.db_queue.put({
                'action': 'remove',
                'order': processed_order
            })
            self.logger.info(f"Queued remove_order to database: {order_id}")
            
            # Call callback for GUI update AFTER queueing
            if self.callback:
                self.callback({
                    'action': 'remove',
                    'order': processed_order
                })
                self.logger.debug(f"GUI callback triggered for remove_order: {order_id}")
                
        except Exception as e:
            self.logger.error(f"Error processing remove_order: {str(e)}")
            self.logger.exception("Full traceback:")
       
    def disconnect(self):
        """Disconnect WebSocket and wait for queue to be processed"""
        self.running = False
        try:
            # Wait for all queued database operations to complete
            self.logger.info("Waiting for database queue to be processed...")
            self.db_queue.join()
            self.logger.info("Database queue processing complete")
            
            # Disconnect WebSocket
            if self.sio.connected:
                self.sio.disconnect()
                self.logger.info("WebSocket disconnected")
                
        except Exception as e:
            self.logger.error(f"Error disconnecting WebSocket: {e}")

    def is_connected(self):
        """Check if socket is connected"""
        return self.connected and self.sio.connected