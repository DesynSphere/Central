# https://forum.arduino.cc/t/two-ways-communication-between-python3-and-arduino/1219738?_gl=1*1hkexoz*_up*MQ..*_ga*MTU5MzU0MzgxNS4xNzY1OTEyNzI3*_ga_NEXN8H46L5*czE3NjU5MTI3MjUkbzEkZzAkdDE3NjU5MTI3MjUkajYwJGwwJGgyMTAxOTE1MzEy

import serial, sys, time, threading, queue
import serial.tools.list_ports

class SerialWorker(threading.Thread):
    # Background thread that reads from a serial port and puts data in a queue.   
    def __init__(self, ser, out_queue, stop_event):
        super().__init__(daemon=True)
        self.ser = ser
        self.out_queue = out_queue
        self.stop_event = stop_event

    def run(self):
        buf = bytearray()
        while not self.stop_event.is_set():
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    buf.extend(data)
                    while b"\n" in buf:
                        line, _, buf = buf.partition(b"\n")
                        try:
                            text = line.decode(errors="replace").strip("\r")
                        except Exception:
                            text = str(line)
                        self.out_queue.put(text)
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.out_queue.put(f"[ERROR] Serial read: {e}")
                time.sleep(0.2)

class SerialManager:
    """Manages serial connection and communication."""
    
    def __init__(self):
        self.serial_connection = None
        self.reader_thread = None
        self.reader_stop = threading.Event()
        self.queue = queue.Queue()

    def listPorts(self):
        # Filter out ports with 'n/a' hwid and return list of available serial port devices
        ports = serial.tools.list_ports.comports()
        valid_ports = [port for port in ports if port.hwid != 'n/a']
        if not valid_ports:
            return ["No valid ports found."]
        return [port.name for port in sorted(valid_ports)]

    def connect(self, port, baudrate):
        """
        Connect to a serial port.
        
        Args:
            port: Serial port device (e.g., 'COM1', '/dev/ttyUSB0')
            baudrate: Baud rate (default: 115200)
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            ValueError: If baudrate is invalid
            RuntimeError: If serial module is not available
        """
        if not port:
            raise ValueError("Port cannot be empty")
        
        try:
            self.serial_connection = serial.Serial(port=port, baudrate=baudrate, timeout=0)
            time.sleep(0.1)  # allow port to settle
        except Exception as e:
            self.serial_connection = None
            raise RuntimeError(f"Could not open {port}: {e}")

        self.reader_stop.clear()
        self.reader_thread = SerialWorker(self.serial_connection, self.queue, self.reader_stop)
        self.reader_thread.start()
        
        return True

    def disconnect(self):
        """Disconnect from serial port."""
        try:
            self.reader_stop.set()
            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=1)
        except Exception:
            pass
        
        try:
            if self.serial_connection:
                self.serial_connection.close()
        except Exception:
            pass
        
        self.serial_connection = None
        self.reader_thread = None

        return True

    def isConnected(self):
        """Check if currently connected to a serial port."""
        return self.serial_connection is not None

    def sendCommand(self, text: str):
        """
        Send a line of text to the serial port.
        
        Args:
            text: Text to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.serial_connection:
            return False
        
        try:
            self.serial_connection.write((text.strip() + "\n").encode())
            return True
        except Exception:
            return False

    def getQueue(self):
        """Get the queue for receiving data."""
        return self.queue
