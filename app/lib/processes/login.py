"""
Reset Order Process
Handles the complete workflow to reset an order in RealWorld
"""

import pexpect
import time
import re
import os
import sys
from dotenv import load_dotenv
from lib.functions import setup_logger
load_dotenv()

# Force allocation of a PTY for pexpect
if not sys.stdin.isatty():
    # Running without a TTY (like from Flask), create a pseudo-terminal
    import pty
    master, slave = pty.openpty()
    os.environ['PEXPECT_FORCE_TTY'] = '1'

def rwlogin(username, user_password):
    """
    Login to RealWorld system using pexpect
    
    Args:
        username: Telnet login username
        user_password: Telnet login password
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    logger = setup_logger("login_process")
    child = None
    
    host = os.getenv('RW_HOST', '')
    port = os.getenv('RW_PORT', '23')

    try:
        # Connect to RealWorld via Telnet
        logger.info(f"Connecting to RealWorld at {host}:{port} with user {username}")
        # print(f"\n=== Starting Reset Process for Order: {host} (DC: {distribution_center}) ===\n")
        child = pexpect.spawn(f'telnet {host} {port}', encoding='utf-8', timeout=30)
        
        # Login
        logger.info("Logging into RealWorld system")
        # print("=== Logging in ===")
        child.expect('login:')
        child.sendline(username)
        child.expect('Password:')
        child.sendline(user_password)
        time.sleep(3.5)
        
        if('Login incorrect' in child.before):
            logger.error("Login incorrect. Aborting reset.")
            return False, 'Login incorrect'
        
        logger.info("Login successful")
        return True
        
    except Exception as e:
        print(f"Error during reset process: {e}")
        logger.error(f"Exception during reset process: {e}")
        return False
    
    finally:
        if child:
            try:
                child.close()
            except:
                pass
