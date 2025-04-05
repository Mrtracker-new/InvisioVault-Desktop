#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InvisioVault - A steganography application for hiding files within images
"""

import os
import sys
import json
import base64
import hashlib
import datetime
import binascii
from io import BytesIO
from typing import Tuple, List, Dict, Optional, Union

import numpy as np
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit,
                             QProgressBar, QMessageBox, QCheckBox, QListWidget, QGroupBox,
                             QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSplitter, QFrame, QTextEdit, QComboBox, QStackedWidget)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer

# Constants
APP_NAME = "InvisioVault"
APP_VERSION = "1.0.0"
MAX_PASSWORD_ATTEMPTS = 3
ENCRYPTION_HEADER = b"INVISIOVAULT"
AES_MODE = AES.MODE_CBC


class SteganographyEngine:
    """Core engine for steganography operations"""
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Derive encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return key, salt
    
    @staticmethod
    def encrypt_data(data: bytes, password: str) -> bytes:
        """Encrypt data with password"""
        salt = os.urandom(16)
        key, _ = SteganographyEngine.derive_key(password, salt)
        iv = os.urandom(16)
        cipher = AES.new(key, AES_MODE, iv)
        encrypted_data = cipher.encrypt(pad(data, AES.block_size))
        # Format: HEADER + SALT + IV + ENCRYPTED_DATA
        return ENCRYPTION_HEADER + salt + iv + encrypted_data
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, password: str) -> bytes:
        """Decrypt data with password"""
        if not encrypted_data.startswith(ENCRYPTION_HEADER):
            raise ValueError("Invalid data format")
        
        # Extract components
        data = encrypted_data[len(ENCRYPTION_HEADER):]
        salt = data[:16]
        iv = data[16:32]
        actual_encrypted_data = data[32:]
        
        # Derive key and decrypt
        key, _ = SteganographyEngine.derive_key(password, salt)
        cipher = AES.new(key, AES_MODE, iv)
        try:
            decrypted_data = unpad(cipher.decrypt(actual_encrypted_data), AES.block_size)
            return decrypted_data
        except (ValueError, KeyError):
            raise ValueError("Incorrect password or corrupted data")
    
    @staticmethod
    def prepare_file_data(file_path: str, password: Optional[str] = None) -> bytes:
        """Prepare file data for hiding"""
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Create metadata
        metadata = {
            "filename": os.path.basename(file_path),
            "size": len(file_data),
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        # Combine metadata and file data
        metadata_bytes = json.dumps(metadata).encode()
        metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
        combined_data = metadata_length + metadata_bytes + file_data
        
        # Encrypt if password provided
        if password:
            return SteganographyEngine.encrypt_data(combined_data, password)
        return combined_data
    
    @staticmethod
    def extract_file_data(data: bytes, password: Optional[str] = None) -> Tuple[Dict, bytes]:
        """Extract file metadata and content from data"""
        # Decrypt if needed
        if password and data.startswith(ENCRYPTION_HEADER):
            try:
                data = SteganographyEngine.decrypt_data(data, password)
            except ValueError:
                raise ValueError("Incorrect password or corrupted data")
        
        # Extract metadata
        metadata_length = int.from_bytes(data[:4], byteorder='big')
        metadata_bytes = data[4:4+metadata_length]
        file_data = data[4+metadata_length:]
        
        try:
            metadata = json.loads(metadata_bytes.decode())
            return metadata, file_data
        except json.JSONDecodeError:
            raise ValueError("Invalid metadata format")
    
    @staticmethod
    def can_hide_data(image_path: str, data_size: int) -> bool:
        """Check if the image can hide the data"""
        try:
            with Image.open(image_path) as img:
                # Each pixel can hide 3 bits (1 in each RGB channel)
                max_bytes = (img.width * img.height * 3) // 8
                # Reserve space for size information (4 bytes)
                return max_bytes >= data_size + 4
        except Exception:
            return False
    
    @staticmethod
    def hide_data_in_image(image_path: str, output_path: str, data: bytes) -> bool:
        """Hide data in image using LSB steganography"""
        try:
            # Open the image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert image to numpy array for faster processing
            pixels = np.array(img)
            
            # Prepare data with size prefix
            data_size = len(data).to_bytes(4, byteorder='big')
            full_data = data_size + data
            
            # Check if image is large enough
            if not SteganographyEngine.can_hide_data(image_path, len(full_data)):
                return False
            
            # Convert data to bit array
            bits = []
            for byte in full_data:
                for i in range(8):
                    bits.append((byte >> i) & 1)
            
            # Pad bits array to ensure we have enough bits
            while len(bits) % 3 != 0:
                bits.append(0)
            
            # Hide data in image
            idx = 0
            for i in range(pixels.shape[0]):
                for j in range(pixels.shape[1]):
                    if idx < len(bits):
                        # Modify the least significant bit of each color channel
                        for k in range(min(3, len(bits) - idx)):
                            # Ensure we're working with valid uint8 values
                            pixels[i, j, k] = (pixels[i, j, k] & 254) | bits[idx + k]
                        idx += 3
                    else:
                        break
                if idx >= len(bits):
                    break
            
            # Save the modified image
            Image.fromarray(pixels).save(output_path)
            return True
        except Exception as e:
            print(f"Error hiding data: {str(e)}")
            return False
    
    @staticmethod
    def extract_data_from_image(image_path: str) -> bytes:
        """Extract hidden data from image"""
        try:
            # Open the image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert image to numpy array for faster processing
            pixels = np.array(img)
            
            # Extract bits from image
            extracted_bits = []
            for i in range(pixels.shape[0]):
                for j in range(pixels.shape[1]):
                    for k in range(3):  # RGB channels
                        # Extract the least significant bit
                        extracted_bits.append(int(pixels[i, j, k] & 1))
                    if len(extracted_bits) >= 32:  # We have enough bits for the size
                        break
                if len(extracted_bits) >= 32:
                    break
            
            # Convert first 32 bits to size value
            size_bits = extracted_bits[:32]
            size_bytes = bytearray()
            for i in range(0, 32, 8):
                byte = 0
                for j in range(8):
                    if i + j < len(size_bits):
                        byte |= (size_bits[i + j] << j)
                size_bytes.append(byte)
            
            data_size = int.from_bytes(size_bytes, byteorder='big')
            total_bits_needed = 32 + (data_size * 8)  # Size bits + data bits
            
            # Extract remaining bits if needed
            while len(extracted_bits) < total_bits_needed:
                i = (len(extracted_bits) // 3) // pixels.shape[1]
                j = (len(extracted_bits) // 3) % pixels.shape[1]
                if i >= pixels.shape[0]:
                    break
                for k in range(3):  # RGB channels
                    if len(extracted_bits) < total_bits_needed:
                        # Extract the least significant bit consistently
                        extracted_bits.append(int(pixels[i, j, k] & 1))
            
            # Convert data bits to bytes
            data_bits = extracted_bits[32:total_bits_needed]
            data_bytes = bytearray()
            for i in range(0, len(data_bits), 8):
                if i + 8 <= len(data_bits):
                    byte = 0
                    for j in range(8):
                        byte |= (data_bits[i + j] << j)
                    data_bytes.append(byte)
            
            return bytes(data_bytes)
        except Exception as e:
            print(f"Error extracting data: {str(e)}")
            return b''


class WorkerThread(QThread):
    """Worker thread for background processing"""
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, task_type, params):
        super().__init__()
        self.task_type = task_type
        self.params = params
    
    def run(self):
        try:
            if self.task_type == "hide":
                self._hide_files()
            elif self.task_type == "extract":
                self._extract_files()
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, str(e))
    
    def _hide_files(self):
        image_path = self.params["image_path"]
        output_path = self.params["output_path"]
        files = self.params["files"]
        password = self.params.get("password")
        
        try:
            # Prepare all files data
            all_files_data = []
            total_size = 0
            
            for i, file_path in enumerate(files):
                self.status_signal.emit(f"Preparing file {i+1}/{len(files)}: {os.path.basename(file_path)}")
                file_data = SteganographyEngine.prepare_file_data(file_path, None)  # Don't encrypt individual files
                all_files_data.append(file_data)
                total_size += len(file_data)
                self.progress_signal.emit(int((i+1) / len(files) * 50))  # First 50% for preparation
            
            # Combine all files data
            combined_data = len(all_files_data).to_bytes(4, byteorder='big')
            for data in all_files_data:
                size = len(data).to_bytes(4, byteorder='big')
                combined_data += size + data
            
            # Encrypt the combined data if password provided
            if password:
                self.status_signal.emit("Encrypting data...")
                combined_data = SteganographyEngine.encrypt_data(combined_data, password)
            
            # Check if image can hold the data
            if not SteganographyEngine.can_hide_data(image_path, len(combined_data)):
                raise ValueError("The selected image is too small to hide all the data")
            
            # Hide data in image
            self.status_signal.emit("Hiding data in image...")
            success = SteganographyEngine.hide_data_in_image(image_path, output_path, combined_data)
            self.progress_signal.emit(100)
            
            if success:
                self.status_signal.emit("Files successfully hidden in image")
                self.finished_signal.emit(True, output_path)
            else:
                self.status_signal.emit("Failed to hide files in image")
                self.finished_signal.emit(False, "Operation failed")
                
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, str(e))
    
    def _extract_files(self):
        image_path = self.params["image_path"]
        output_dir = self.params["output_dir"]
        password = self.params.get("password")
        
        try:
            # Extract data from image
            self.status_signal.emit("Extracting data from image...")
            data = SteganographyEngine.extract_data_from_image(image_path)
            if not data:
                raise ValueError("No hidden data found in the image")
            self.progress_signal.emit(30)
            
            # Decrypt data if needed
            if data.startswith(ENCRYPTION_HEADER):
                if not password:
                    raise ValueError("This image contains encrypted data. Please provide a password.")
                self.status_signal.emit("Decrypting data...")
                try:
                    data = SteganographyEngine.decrypt_data(data, password)
                except ValueError:
                    raise ValueError("Incorrect password or corrupted data")
            self.progress_signal.emit(50)
            
            # Extract files from data
            num_files = int.from_bytes(data[:4], byteorder='big')
            self.status_signal.emit(f"Found {num_files} hidden files")
            
            # Parse the data to extract individual files
            offset = 4
            extracted_files = []
            
            for i in range(num_files):
                if offset >= len(data):
                    break
                    
                # Get file size
                file_size = int.from_bytes(data[offset:offset+4], byteorder='big')
                offset += 4
                
                # Get file data
                file_data = data[offset:offset+file_size]
                offset += file_size
                
                # Extract metadata and content
                try:
                    metadata, content = SteganographyEngine.extract_file_data(file_data, None)  # Already decrypted
                    file_path = os.path.join(output_dir, metadata["filename"])
                    
                    # Ensure filename is unique
                    base, ext = os.path.splitext(file_path)
                    counter = 1
                    while os.path.exists(file_path):
                        file_path = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    # Save the file
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    extracted_files.append(file_path)
                    self.status_signal.emit(f"Extracted: {os.path.basename(file_path)}")
                except Exception as e:
                    self.status_signal.emit(f"Error extracting file {i+1}: {str(e)}")
                
                self.progress_signal.emit(50 + int((i+1) / num_files * 50))  # Last 50% for extraction
            
            self.status_signal.emit(f"Successfully extracted {len(extracted_files)} files")
            self.finished_signal.emit(True, "\n".join(extracted_files))
                
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, str(e))


class SplashScreen(QWidget):
    """Splash screen showing application branding"""
    
    def __init__(self):
        super().__init__()
        self.fade_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.fade_effect)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)
        self.glow_value = 0
        self.glow_direction = 1
    
    def update_glow(self):
        self.glow_value += 0.02 * self.glow_direction
        if self.glow_value >= 1.0:
            self.glow_value = 1.0
            self.glow_direction = -1
        elif self.glow_value <= 0.3:
            self.glow_value = 0.3
            self.glow_direction = 1
            
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"""
                color: #ffffff;
                font-weight: bold;
                font-size: 48px;
                text-shadow: 0 0 10px #0cebf0;
                background-color: rgba(15, 15, 35, 1.0);
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #0cebf0;
            """)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)
        
        title_container = QFrame()
        title_container.setFrameShape(QFrame.StyledPanel)
        title_container.setStyleSheet("""
            border: 2px solid rgba(12, 235, 240, 0.3);
            border-radius: 20px;
            background-color: rgba(15, 15, 35, 1.0);
            padding: 20px;
        """)
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(15)
        
        self.title_label = QLabel("InvisioVault")
        title_font = QFont("Arial, sans-serif")
        title_font.setPointSize(48)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #0cebf0; 
            font-weight: bold;
            background-color: rgba(0,0,0,1.0);
            padding: 10px;
            border-radius: 10px;
        """)
        title_layout.addWidget(self.title_label)
        
        author_label = QLabel("By Rolan")
        author_font = QFont("Arial, sans-serif")
        author_font.setPointSize(20)
        author_font.setItalic(True)
        author_label.setFont(author_font)
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setContentsMargins(10, 5, 10, 5)
        author_label.setStyleSheet("""
            color: #0cebf0;
            background-color: rgba(0,0,0,1.0);
            padding: 8px;
            border-radius: 8px;
            font-weight: 500;
        """)
        title_layout.addWidget(author_label)
        
        layout.addWidget(title_container)
        layout.addSpacing(30)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7a04eb, stop:1 #0cebf0); 
            border: none; 
            height: 2px; 
            margin: 50px;
            border-radius: 1px;
        """)
        layout.addWidget(line)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_font = QFont("Arial, sans-serif")
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            color: #ffffff;
            margin-top: 15px;
            background-color: rgba(0,0,0,1.0);
            padding: 8px;
            border-radius: 8px;
            font-weight: bold;
        """)
        layout.addWidget(version_label)
        
        tagline = QLabel("Secure Steganography Solution")
        tagline_font = QFont("Arial, sans-serif")
        tagline_font.setPointSize(14)
        tagline.setFont(tagline_font)
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("""
            color: #ffffff;
            margin: 15px 40px;
            font-weight: bold;
            background-color: rgba(0,0,0,0.95);
            padding: 15px;
            border-radius: 10px;
            font-size: 16px;
        """)
        layout.addWidget(tagline)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 35, 1.0);
                color: #ffffff;
            }
            QLabel, QPushButton {
                background-color: #1a1a3a;
                border: 1px solid #0cebf0;
                padding: 8px;
            }
        """)


class DisclaimerScreen(QWidget):
    """Disclaimer screen showing legal information"""
    
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        
        # Create fade effect for animations
        self.fade_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.fade_effect)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setup_ui()
        
        # Ensure solid background
        self.setWindowOpacity(1.0)
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WA_ShowWithoutActivating)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title_label = QLabel("DISCLAIMER")
        title_font = QFont("Arial, sans-serif")
        title_font.setPointSize(32)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #0cebf0; 
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
            background-color: #0cebf0; 
            border: none; 
            height: 2px; 
            margin: 0 50px;
            border-radius: 1px;
        """)
        layout.addWidget(line)
        
        disclaimer_text = QTextEdit()
        disclaimer_text.setReadOnly(True)
        disclaimer_text.setMinimumHeight(250)
        disclaimer_text.setHtml("""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #e0e0ff;">
            <p style="margin-bottom: 15px;">This software is provided for educational and personal use only.</p>
            
            <p style="margin-bottom: 15px;"><b style="color: #0cebf0;">Important:</b> The use of steganography tools may be subject to legal restrictions in some jurisdictions. 
            Users are responsible for ensuring their use of this software complies with all applicable laws.</p>
            
            <p style="margin-bottom: 15px;">The creator of InvisioVault is not responsible for any misuse of this software or any damages 
            that may result from its use.</p>
            
            <p style="margin-bottom: 15px;">By continuing, you acknowledge that you understand and accept these terms.</p>
        </div>
        """)
        disclaimer_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 10, 30, 1.0);
                border: 2px solid #0cebf0;
                border-radius: 10px;
                padding: 20px;
                color: #ffffff;
                font-size: 10pt;
                selection-background-color: rgba(122, 4, 235, 0.5);
                selection-color: #ffffff;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(30, 30, 60, 0.3);
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7a04eb, stop:1 #0cebf0);
                min-height: 20px;
                border-radius: 6px;
            }
        """)
        layout.addWidget(disclaimer_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.continue_button = QPushButton("I UNDERSTAND - CONTINUE")
        self.continue_button.setMinimumWidth(300)
        self.continue_button.setMinimumHeight(50)
        button_font = QFont("Arial, sans-serif", 11)
        button_font.setBold(True)
        self.continue_button.setFont(button_font)
        self.continue_button.clicked.connect(self.continue_clicked)
        self.continue_button.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        button_layout.addWidget(self.continue_button)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 35, 1.0);
                color: #ffffff;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7a04eb, stop:1 #0cebf0);
                color: #ffffff;
                border: none;
                padding: 12px 24px;
                border-radius: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a14fb, stop:1 #1cfbff);
                border: 2px solid #ffffff;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6a04cb, stop:1 #0ca9b0);
                color: #ffffff;
            }
            QLabel {
                color: #e0e0ff;
            }
            QLineEdit, QTextEdit, QListWidget, QTableWidget {
                background-color: rgba(12, 12, 30, 1.0);
                color: #ffffff;
                border: 2px solid #0cebf0;
                border-radius: 10px;
                padding: 10px;
                font-size: 10pt;
            }
            QGroupBox {
                border: 2px solid #0cebf0;
                border-radius: 10px;
                margin-top: 2.5ex;
                padding-top: 2.5ex;
                background-color: rgba(15, 15, 35, 0.7);
                font-size: 11pt;
            }
            QTabWidget::pane {
                border: 2px solid #0cebf0;
                background-color: rgba(8, 8, 25, 0.9);
                border-radius: 10px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: rgba(25, 25, 55, 0.8);
                color: #e6e6ff;
                padding: 12px 30px;
                border: 1px solid #0cebf0;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-family: Arial, sans-serif;
                font-weight: bold;
                letter-spacing: 0.5px;
                margin-right: 3px;
                min-width: 120px;
                text-align: center;
            }
            QTabBar::tab:selected {
                background-color: rgba(12, 12, 30, 0.9);
                border-bottom: 3px solid #0cebf0;
                color: #0cebf0;
            }
        """)
    
    def continue_clicked(self):
        if self.controller:
            self.controller.show_main_app()
        else:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'show_main_app'):
                    parent.show_main_app()
                    break
                parent = parent.parent()
                
    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'continue_button'):
            self.continue_button.setStyleSheet("""
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7a04eb, stop:1 #0cebf0);
                color: #ffffff;
                border: none;
                padding: 12px 24px;
                border-radius: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
                font-weight: bold;
                font-size: 12pt;
            """)
            self.continue_button.setVisible(True)


class AppController(QMainWindow):
    """Main application controller managing screen transitions"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 700)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "InvisioVault.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #08081a, stop:1 #1a1a3a);
                border: 1px solid #0cebf0;
            }
        """)
        
        self.background_timer = QTimer(self)
        self.background_timer.timeout.connect(self.update_background)
        self.background_timer.start(50)
        self.background_offset = 0
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.splash_screen = SplashScreen()
        self.disclaimer_screen = DisclaimerScreen(controller=self)
        self.main_app = MainWindow()
        
        self.stacked_widget.addWidget(self.splash_screen)
        self.stacked_widget.addWidget(self.disclaimer_screen)
        self.stacked_widget.addWidget(self.main_app)
        
        self.stacked_widget.setCurrentWidget(self.splash_screen)
        
        QTimer.singleShot(2500, self.show_disclaimer)
    
    def update_background(self):
        self.background_offset += 1
        if self.background_offset > 100:
            self.background_offset = 0
    
    def show_disclaimer(self):
        self.fade_out = QtCore.QPropertyAnimation(self.splash_screen.fade_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.start()
        
        self.disclaimer_screen.setVisible(False)
        if hasattr(self.disclaimer_screen, 'fade_effect'):
            self.disclaimer_screen.fade_effect.setOpacity(0.0)
        
        self.fade_out.finished.connect(lambda: self._switch_to_screen(self.disclaimer_screen))
    
    def show_main_app(self):
        self.fade_out = QtCore.QPropertyAnimation(self.disclaimer_screen.fade_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.start()
        
        self.main_app.setVisible(False)
        if hasattr(self.main_app, 'fade_effect'):
            self.main_app.fade_effect.setOpacity(0.0)
        
        self.fade_out.finished.connect(lambda: self._switch_to_screen(self.main_app))
    
    def _switch_to_screen(self, screen):
        if screen == self.disclaimer_screen:
            self.disclaimer_screen.controller = self
        
        if hasattr(screen, 'fade_effect'):
            screen.fade_effect.setOpacity(0.0)
        
        self.stacked_widget.setCurrentWidget(screen)
        screen.setVisible(True)
        
        if hasattr(screen, 'fade_effect'):
            fade_in = QtCore.QPropertyAnimation(screen.fade_effect, b"opacity")
            fade_in.setDuration(0)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.start()
            fade_in.finished.connect(lambda: self._ensure_screen_visible(screen))
    
    def _ensure_screen_visible(self, screen):
        if hasattr(screen, 'fade_effect'):
            screen.fade_effect.setOpacity(1.0)
        screen.setVisible(True)
        screen.setFocus()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 700)
        
        # Remove opacity effect completely
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WA_ShowWithoutActivating)
        
        self.setup_style()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        self.hide_tab = QWidget()
        self.extract_tab = QWidget()
        self.history_tab = QWidget()
        self.about_tab = QWidget()
        
        self.tabs.addTab(self.hide_tab, "Hide Files")
        self.tabs.addTab(self.extract_tab, "Extract Files")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.about_tab, "About")
        
        self.setup_hide_tab()
        self.setup_extract_tab()
        self.setup_history_tab()
        self.setup_about_tab()
        
        self.history = self.load_history()
        self.update_history_table()
        
        self.statusBar().showMessage("Ready")

    def setup_style(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(8, 8, 25))
        dark_palette.setColor(QPalette.WindowText, QColor(230, 230, 255))
        dark_palette.setColor(QPalette.Base, QColor(12, 12, 30))
        dark_palette.setColor(QPalette.AlternateBase, QColor(18, 18, 40))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(230, 230, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(230, 230, 255))
        dark_palette.setColor(QPalette.Text, QColor(230, 230, 255))
        dark_palette.setColor(QPalette.Button, QColor(25, 25, 55))
        dark_palette.setColor(QPalette.ButtonText, QColor(240, 240, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(12, 235, 240))
        dark_palette.setColor(QPalette.Link, QColor(12, 235, 240))
        dark_palette.setColor(QPalette.Highlight, QColor(122, 4, 235))
        dark_palette.setColor(QPalette.HighlightedText, QColor(240, 240, 255))
        
        self.setPalette(dark_palette)
        
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #08081a, stop:0.5 #0c0c25, stop:1 #15153a);
                color: #e6e6ff;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border: 2px solid #0cebf0;
                background-color: rgba(8, 8, 25, 0.9);
                border-radius: 10px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: rgba(25, 25, 55, 0.8);
                color: #e6e6ff;
                padding: 12px 30px;
                border: 1px solid #0cebf0;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-family: Arial, sans-serif;
                font-weight: bold;
                letter-spacing: 0.5px;
                margin-right: 3px;
                min-width: 120px;
                text-align: center;
            }
            QTabBar::tab:selected {
                background-color: rgba(12, 12, 30, 0.9);
                border-bottom: 3px solid #0cebf0;
                color: #0cebf0;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(35, 35, 70, 0.8);
                color: #0cebf0;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7a04eb, stop:1 #0cebf0);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                font-family: Arial, sans-serif;
                font-weight: bold;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a14fb, stop:1 #1cfbff);
                border: 2px solid #ffffff;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6a04cb, stop:1 #0ca9b0);
                color: #e0e0ff;
            }
            QPushButton:disabled {
                background-color: #1a1a35;
                color: #8a8aaa;
            }
            QLineEdit, QTextEdit, QListWidget, QTableWidget {
                background-color: rgba(12, 12, 30, 1.0);
                color: #e6e6ff;
                border: 2px solid #0cebf0;
                border-radius: 10px;
                padding: 10px;
                font-size: 10pt;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #7a04eb;
                background-color: rgba(15, 15, 35, 0.9);
            }
            QProgressBar {
                border: 2px solid #0cebf0;
                border-radius: 10px;
                text-align: center;
                background-color: rgba(12, 12, 30, 1.0);
                height: 24px;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7a04eb, stop:1 #0cebf0);
                border-radius: 8px;
            }
            QGroupBox {
                border: 2px solid #0cebf0;
                border-radius: 10px;
                margin-top: 2.5ex;
                padding-top: 2.5ex;
                background-color: rgba(15, 15, 35, 0.7);
                font-size: 11pt;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 15px;
                color: #0cebf0;
                font-weight: bold;
                font-size: 11pt;
                letter-spacing: 1px;
            }
            QLabel {
                color: #e6e6ff;
                font-size: 10pt;
            }
            QCheckBox {
                color: #e6e6ff;
                spacing: 10px;
                font-size: 10pt;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #0cebf0;
                border-radius: 5px;
                background-color: rgba(12, 12, 30, 1.0);
            }
            QCheckBox::indicator:checked {
                background-color: #0cebf0;
            }
            QRadioButton {
                color: #e6e6ff;
                spacing: 10px;
                font-size: 10pt;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #0cebf0;
                border-radius: 10px;
                background-color: rgba(12, 12, 30, 1.0);
            }
            QRadioButton::indicator:checked {
                background-color: rgba(12, 12, 30, 1.0);
            }
            QTableWidget {
                gridline-color: #0cebf0;
                selection-background-color: rgba(122, 4, 235, 0.4);
                alternate-background-color: rgba(20, 20, 40, 0.5);
            }
            QHeaderView::section {
                background-color: rgba(25, 25, 55, 0.8);
                color: #e6e6ff;
                padding: 8px;
                border: 1px solid #0cebf0;
                font-weight: bold;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(12, 12, 30, 0.3);
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7a04eb, stop:1 #0cebf0);
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar:horizontal {
                border: none;
                background: rgba(12, 12, 30, 0.3);
                height: 14px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7a04eb, stop:1 #0cebf0);
                min-width: 30px;
                border-radius: 7px;
            }
            #hide_image_preview, #extract_image_preview {
                background-color: rgba(8, 8, 20, 0.8);
                border: 2px solid #0cebf0;
                border-radius: 10px;
                padding: 5px;
            }
        """)
    
    def setup_hide_tab(self):
        layout = QVBoxLayout(self.hide_tab)
        
        image_group = QGroupBox("Carrier Image")
        image_layout = QVBoxLayout(image_group)
        
        image_select_layout = QHBoxLayout()
        self.hide_image_path = QLineEdit()
        self.hide_image_path.setReadOnly(True)
        self.hide_image_path.setPlaceholderText("Select an image file...")
        image_select_layout.addWidget(self.hide_image_path)
        
        browse_image_btn = QPushButton("Browse")
        browse_image_btn.clicked.connect(self.browse_hide_image)
        image_select_layout.addWidget(browse_image_btn)
        
        image_layout.addLayout(image_select_layout)
        
        self.hide_image_preview = QLabel("No image selected")
        self.hide_image_preview.setAlignment(Qt.AlignCenter)
        self.hide_image_preview.setMinimumHeight(180)

        self.hide_image_preview.setObjectName("hide_image_preview")
        image_layout.addWidget(self.hide_image_preview)
        
        layout.addWidget(image_group)
        
        files_group = QGroupBox("Files to Hide")
        files_layout = QVBoxLayout(files_group)
        
        files_select_layout = QHBoxLayout()
        self.hide_files_list = QListWidget()
        files_select_layout.addWidget(self.hide_files_list)
        
        files_buttons_layout = QVBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.add_files_to_hide)
        files_buttons_layout.addWidget(add_files_btn)
        
        remove_files_btn = QPushButton("Remove Selected")
        remove_files_btn.clicked.connect(self.remove_selected_files)
        files_buttons_layout.addWidget(remove_files_btn)
        
        clear_files_btn = QPushButton("Clear All")
        clear_files_btn.clicked.connect(self.clear_files_list)
        files_buttons_layout.addWidget(clear_files_btn)
        
        files_buttons_layout.addStretch()
        files_select_layout.addLayout(files_buttons_layout)
        
        files_layout.addLayout(files_select_layout)
        
        layout.addWidget(files_group)
        
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.hide_password = QLineEdit()
        self.hide_password.setEchoMode(QLineEdit.Password)
        self.hide_password.setPlaceholderText("Leave empty for no encryption")
        password_layout.addWidget(self.hide_password)
        
        options_layout.addLayout(password_layout)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Image:"))
        self.hide_output_path = QLineEdit()
        self.hide_output_path.setReadOnly(True)
        self.hide_output_path.setPlaceholderText("Will be set automatically")
        output_layout.addWidget(self.hide_output_path)
        
        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self.browse_hide_output)
        output_layout.addWidget(browse_output_btn)
        
        options_layout.addLayout(output_layout)
        
        layout.addWidget(options_group)
        
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.hide_progress_bar = QProgressBar()
        self.hide_progress_bar.setValue(0)
        progress_layout.addWidget(self.hide_progress_bar)
        
        self.hide_status_label = QLabel("Ready")
        progress_layout.addWidget(self.hide_status_label)
        
        layout.addWidget(progress_group)
        
        buttons_layout = QHBoxLayout()
        
        hide_files_btn = QPushButton("Hide Files")
        hide_files_btn.clicked.connect(self.start_hiding_files)
        buttons_layout.addWidget(hide_files_btn)
        
        layout.addLayout(buttons_layout)
    
    def setup_extract_tab(self):
        layout = QVBoxLayout(self.extract_tab)
        
        image_group = QGroupBox("Image with Hidden Data")
        image_layout = QVBoxLayout(image_group)
        
        image_select_layout = QHBoxLayout()
        self.extract_image_path = QLineEdit()
        self.extract_image_path.setReadOnly(True)
        self.extract_image_path.setPlaceholderText("Select an image file...")
        image_select_layout.addWidget(self.extract_image_path)
        
        browse_image_btn = QPushButton("Browse")
        browse_image_btn.clicked.connect(self.browse_extract_image)
        image_select_layout.addWidget(browse_image_btn)
        
        image_layout.addLayout(image_select_layout)
        
        self.extract_image_preview = QLabel("No image selected")
        self.extract_image_preview.setAlignment(Qt.AlignCenter)
        self.extract_image_preview.setMinimumHeight(180)
        self.extract_image_preview.setObjectName("extract_image_preview")
        image_layout.addWidget(self.extract_image_preview)
        
        layout.addWidget(image_group)
        
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.extract_password = QLineEdit()
        self.extract_password.setEchoMode(QLineEdit.Password)
        self.extract_password.setPlaceholderText("Enter password if required")
        password_layout.addWidget(self.extract_password)
        
        options_layout.addLayout(password_layout)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Directory:"))
        self.extract_output_dir = QLineEdit()
        self.extract_output_dir.setReadOnly(True)
        self.extract_output_dir.setPlaceholderText("Select output directory...")
        output_layout.addWidget(self.extract_output_dir)
        
        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self.browse_extract_output)
        output_layout.addWidget(browse_output_btn)
        
        options_layout.addLayout(output_layout)
        
        layout.addWidget(options_group)
        
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.extract_progress_bar = QProgressBar()
        self.extract_progress_bar.setValue(0)
        progress_layout.addWidget(self.extract_progress_bar)
        
        self.extract_status_label = QLabel("Ready")
        progress_layout.addWidget(self.extract_status_label)
        
        layout.addWidget(progress_group)
        
        buttons_layout = QHBoxLayout()
        
        extract_files_btn = QPushButton("Extract Files")
        extract_files_btn.clicked.connect(self.start_extracting_files)
        buttons_layout.addWidget(extract_files_btn)
        
        layout.addLayout(buttons_layout)
    
    def setup_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Operation", "Image", "Files", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.history_table)
        
        buttons_layout = QHBoxLayout()
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self.clear_history)
        buttons_layout.addWidget(clear_history_btn)
        
        layout.addLayout(buttons_layout)
    
    def setup_about_tab(self):
        layout = QVBoxLayout(self.about_tab)
        layout.setSpacing(20)
        
        title_container = QFrame()
        title_container.setFrameShape(QFrame.StyledPanel)
        title_container.setStyleSheet("""
            border: 2px solid rgba(12, 235, 240, 0.3);
            border-radius: 15px;
            background-color: rgba(15, 15, 35, 1.0);
            padding: 20px;
            margin-bottom: 10px;
        """)
        title_layout = QVBoxLayout(title_container)
        
        app_info = QLabel(f"<h1>{APP_NAME}</h1>")
        app_info_font = QFont("Arial, sans-serif", 24)
        app_info_font.setBold(True)
        app_info.setFont(app_info_font)
        app_info.setAlignment(Qt.AlignCenter)
        app_info.setStyleSheet("""
            color: #0cebf0; 
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        """)
        title_layout.addWidget(app_info)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_font = QFont("Arial, sans-serif", 12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            color: #7a04eb; 
            letter-spacing: 1px;
            margin-bottom: 10px;
        """)
        title_layout.addWidget(version_label)
        
        layout.addWidget(title_container)
        
        description = QLabel(
            "<p>InvisioVault is a steganography application that allows you to hide various "
            "file types (PDF, media, documents, etc.) within image files. The hidden files "
            "can be protected with password encryption for added security.</p>"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("""
            font-size: 11pt;
            color: #e6e6ff;
            background-color: rgba(15, 15, 35, 0.3);
            border-radius: 10px;
            padding: 15px;
            line-height: 1.4;
        """)
        layout.addWidget(description)
        
        features_group = QGroupBox("Features")
        features_group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
            }
        """)
        features_layout = QVBoxLayout(features_group)
        
        features_text = QLabel(
            "<div style='line-height: 1.6;'>"
            "<ul>"
            "<li><span style='color: #0cebf0;'>Hide</span> any file type within image files (PNG, JPG, BMP)</li>"
            "<li><span style='color: #0cebf0;'>Extract</span> hidden files from images</li>"
            "<li><span style='color: #0cebf0;'>Protect</span> with AES-256 encryption</li>"
            "<li><span style='color: #0cebf0;'>Enjoy</span> a user-friendly graphical interface</li>"
            "<li><span style='color: #0cebf0;'>Process</span> multiple files in batch operations</li>"
            "<li><span style='color: #0cebf0;'>Verify</span> file integrity during operations</li>"
            "<li><span style='color: #0cebf0;'>Track</span> history of hidden/extracted files</li>"
            "</ul>"
            "</div>"
        )
        features_text.setWordWrap(True)
        features_text.setStyleSheet("""
            font-size: 11pt;
            padding: 5px;
        """)
        features_layout.addWidget(features_text)
        
        layout.addWidget(features_group)
        
        disclaimer_group = QGroupBox("Disclaimer")
        disclaimer_layout = QVBoxLayout(disclaimer_group)
        
        disclaimer_text = QLabel(
            "<p style='line-height: 1.5;'><span style='color: #0cebf0; font-weight: bold;'>Important:</span> "
            "This tool is intended for legitimate privacy and security purposes only. "
            "Users are responsible for ensuring they comply with all applicable laws "
            "regarding data privacy and security.</p>"
        )
        disclaimer_text.setWordWrap(True)
        disclaimer_text.setStyleSheet("font-size: 11pt;")
        disclaimer_layout.addWidget(disclaimer_text)
        
        layout.addWidget(disclaimer_group)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7a04eb, stop:1 #0cebf0); 
            border: none; 
            height: 2px; 
            margin: 10px 30px;
            border-radius: 1px;
        """)
        layout.addWidget(line)
        
        copyright_label = QLabel("© 2025 Rolan. All rights reserved.")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #7a04eb; font-size: 10pt;")
        layout.addWidget(copyright_label)
        
        layout.addStretch()
    
    def browse_hide_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Carrier Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.hide_image_path.setText(file_path)
            self.update_image_preview(file_path, self.hide_image_preview)
            
            if not self.hide_output_path.text():
                dir_path, file_name = os.path.split(file_path)
                name, ext = os.path.splitext(file_name)
                output_path = os.path.join(dir_path, f"{name}_hidden{ext}")
                self.hide_output_path.setText(output_path)
    
    def browse_hide_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.hide_output_path.setText(file_path)
    
    def add_files_to_hide(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Hide", "", "All Files (*.*)"
        )
        for file_path in file_paths:
            if not self.hide_files_list.findItems(file_path, Qt.MatchExactly):
                self.hide_files_list.addItem(file_path)
    
    def remove_selected_files(self):
        for item in self.hide_files_list.selectedItems():
            self.hide_files_list.takeItem(self.hide_files_list.row(item))
    
    def clear_files_list(self):
        self.hide_files_list.clear()
    
    def browse_extract_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image with Hidden Data", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.extract_image_path.setText(file_path)
            self.update_image_preview(file_path, self.extract_image_preview)
    
    def browse_extract_output(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", ""
        )
        if dir_path:
            self.extract_output_dir.setText(dir_path)
    
    def update_image_preview(self, image_path, preview_label):
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    preview_label.width(), preview_label.height(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                preview_label.setPixmap(pixmap)
            else:
                preview_label.setText("Failed to load image")
        except Exception as e:
            preview_label.setText(f"Error: {str(e)}")
    
    def start_hiding_files(self):
        image_path = self.hide_image_path.text()
        if not image_path or not os.path.isfile(image_path):
            QMessageBox.warning(self, "Error", "Please select a valid carrier image.")
            return
        
        output_path = self.hide_output_path.text()
        if not output_path:
            QMessageBox.warning(self, "Error", "Please specify an output image path.")
            return
        
        files = [self.hide_files_list.item(i).text() for i in range(self.hide_files_list.count())]
        if not files:
            QMessageBox.warning(self, "Error", "Please add at least one file to hide.")
            return
        
        for file_path in files:
            if not os.path.isfile(file_path):
                QMessageBox.warning(self, "Error", f"File not found: {file_path}")
                return
        
        password = self.hide_password.text() if self.hide_password.text() else None
        
        params = {
            "image_path": image_path,
            "output_path": output_path,
            "files": files,
            "password": password
        }
        
        self.worker = WorkerThread("hide", params)
        self.worker.progress_signal.connect(self.update_hide_progress)
        self.worker.status_signal.connect(self.update_hide_status)
        self.worker.finished_signal.connect(self.hide_operation_finished)
        
        self.hide_tab.setEnabled(False)
        self.hide_progress_bar.setValue(0)
        self.hide_status_label.setText("Starting operation...")
        
        self.worker.start()
    
    def start_extracting_files(self):
        image_path = self.extract_image_path.text()
        if not image_path or not os.path.isfile(image_path):
            QMessageBox.warning(self, "Error", "Please select a valid image.")
            return
        
        output_dir = self.extract_output_dir.text()
        if not output_dir or not os.path.isdir(output_dir):
            QMessageBox.warning(self, "Error", "Please specify a valid output directory.")
            return
        
        password = self.extract_password.text() if self.extract_password.text() else None
        
        params = {
            "image_path": image_path,
            "output_dir": output_dir,
            "password": password
        }
        
        self.worker = WorkerThread("extract", params)
        self.worker.progress_signal.connect(self.update_extract_progress)
        self.worker.status_signal.connect(self.update_extract_status)
        self.worker.finished_signal.connect(self.extract_operation_finished)
        
        self.extract_tab.setEnabled(False)
        self.extract_progress_bar.setValue(0)
        self.extract_status_label.setText("Starting operation...")
        
        self.worker.start()
    
    def update_hide_progress(self, value):
        self.hide_progress_bar.setValue(value)
    
    def update_hide_status(self, status):
        self.hide_status_label.setText(status)
        self.statusBar().showMessage(status)
    
    def hide_operation_finished(self, success, result):
        self.hide_tab.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, "Success", f"Files successfully hidden in image:\n{result}"
            )
            
            self.add_to_history("Hide", self.hide_image_path.text(), 
                               [self.hide_files_list.item(i).text() for i in range(self.hide_files_list.count())],
                               "Success")
        else:
            QMessageBox.critical(self, "Error", f"Operation failed: {result}")
            
            self.add_to_history("Hide", self.hide_image_path.text(), 
                               [self.hide_files_list.item(i).text() for i in range(self.hide_files_list.count())],
                               f"Failed: {result}")
    
    def update_extract_progress(self, value):
        self.extract_progress_bar.setValue(value)
    
    def update_extract_status(self, status):
        self.extract_status_label.setText(status)
        self.statusBar().showMessage(status)
    
    def extract_operation_finished(self, success, result):
        self.extract_tab.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, "Success", f"Files successfully extracted:\n{result}"
            )
            
            self.add_to_history("Extract", self.extract_image_path.text(), 
                               result.split('\n'),
                               "Success")
        else:
            QMessageBox.critical(self, "Error", f"Operation failed: {result}")
            
            self.add_to_history("Extract", self.extract_image_path.text(), 
                               [],
                               f"Failed: {result}")
    
    def add_to_history(self, operation, image, files, status):
        timestamp = datetime.datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "operation": operation,
            "image": image,
            "files": files,
            "status": status
        }
        
        self.history.append(entry)
        self.save_history()
        self.update_history_table()
    
    def load_history(self):
        history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def save_history(self):
        history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
        try:
            with open(history_path, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {str(e)}")
    
    def update_history_table(self):
        self.history_table.setRowCount(0)
        
        for entry in self.history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            try:
                dt = datetime.datetime.fromisoformat(entry["timestamp"])
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                formatted_time = entry["timestamp"]
            
            files_str = ", ".join([os.path.basename(f) for f in entry["files"]])
            if len(files_str) > 50:
                files_str = files_str[:47] + "..."
            
            self.history_table.setItem(row, 0, QTableWidgetItem(formatted_time))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry["operation"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(os.path.basename(entry["image"])))
            self.history_table.setItem(row, 3, QTableWidgetItem(files_str))
            self.history_table.setItem(row, 4, QTableWidgetItem(entry["status"]))
    
    def clear_history(self):
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to clear the history?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history = []
            self.save_history()
            self.update_history_table()


def main():
    app = QApplication(sys.argv)
    window = AppController()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()