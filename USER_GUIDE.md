# InvisioVault User Guide

Welcome to InvisioVault, a powerful steganography application that allows you to hide various file types within images. This guide will help you get started with the application and explain its features in detail.

## Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Hiding Files](#hiding-files)
4. [Extracting Files](#extracting-files)
5. [Password Protection](#password-protection)
6. [History Tracking](#history-tracking)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

## Installation

### Prerequisites

- Windows operating system
- Python 3.8 or higher (if running from source)

### Option 1: Using the Executable

1. Download the InvisioVault executable from the release page
2. Double-click the executable to run the application

### Option 2: Running from Source

1. Clone or download the InvisioVault repository
2. Open a command prompt in the project directory
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python invisiovault.py
   ```

### Option 3: Building the Executable Yourself

1. Clone or download the InvisioVault repository
2. Open a command prompt in the project directory
3. Run the build script:
   ```
   build.bat
   ```
   or
   ```
   python build.py
   ```
4. The executable will be created in the `dist` folder

## Getting Started

When you first launch InvisioVault, you'll see a user interface with four tabs:

- **Hide Files**: Use this tab to hide files within an image
- **Extract Files**: Use this tab to extract hidden files from an image
- **History**: View a log of your past operations
- **About**: Information about the application

## Hiding Files

To hide files within an image:

1. Go to the **Hide Files** tab
2. Click **Browse** under "Carrier Image" to select an image file (PNG, JPG, or BMP)
3. Click **Add Files** to select one or more files you want to hide
4. (Optional) Enter a password for encryption
5. (Optional) Click **Browse** under "Output Image" to specify where to save the output image
6. Click **Hide Files** to start the process
7. Wait for the operation to complete
8. A success message will appear when the files are hidden

**Note**: The carrier image must be large enough to hold all the files you want to hide. Larger files require larger images.

## Extracting Files

To extract files from an image:

1. Go to the **Extract Files** tab
2. Click **Browse** under "Image with Hidden Data" to select an image containing hidden files
3. (Optional) Enter the password if the hidden data is encrypted
4. Click **Browse** under "Output Directory" to select where to save the extracted files
5. Click **Extract Files** to start the process
6. Wait for the operation to complete
7. A success message will appear when the files are extracted

## Password Protection

InvisioVault uses AES-256 encryption to secure your hidden files. When you hide files with a password:

- The data is encrypted before being hidden in the image
- The same password will be required to extract the files
- Without the correct password, the hidden data cannot be extracted

Password tips:

- Use a strong, unique password
- Longer passwords provide better security
- Include a mix of letters, numbers, and special characters
- Remember your password! If you forget it, the hidden data cannot be recovered

## History Tracking

InvisioVault keeps a record of your operations in the **History** tab:

- **Date**: When the operation was performed
- **Operation**: Whether files were hidden or extracted
- **Image**: The image file used
- **Files**: The files that were hidden or extracted
- **Status**: Whether the operation was successful

You can clear the history by clicking the **Clear History** button.

## Troubleshooting

### Common Issues

1. **"The selected image is too small to hide all the data"**
   - Solution: Use a larger image or reduce the size/number of files you're trying to hide

2. **"No hidden data found in the image"**
   - Solution: Make sure you're selecting an image that actually contains hidden data

3. **"Incorrect password or corrupted data"**
   - Solution: Make sure you're entering the correct password

4. **"This image contains encrypted data. Please provide a password."**
   - Solution: Enter the password that was used to encrypt the data

5. **Application crashes or freezes**
   - Solution: Restart the application and try again with smaller files or a larger image

### Performance Tips

- Hiding and extracting large files may take some time
- PNG images generally work better than JPG for steganography
- Avoid using heavily compressed images as carriers

## Security Best Practices

1. **Keep your carrier images private**
   - Don't share the images containing hidden data publicly

2. **Use strong passwords**
   - Always use a password when hiding sensitive information

3. **Secure storage**
   - Store your carrier images in a secure location

4. **Delete original files**
   - After hiding sensitive files, consider securely deleting the originals

5. **Avoid suspicious patterns**
   - Don't use obvious file names or predictable patterns

---

Thank you for using InvisioVault! If you encounter any issues or have suggestions for improvement, please report them to the project repository.