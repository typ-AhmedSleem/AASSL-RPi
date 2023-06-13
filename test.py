
if __name__ == '__main__':
    import constants
    from aassl import AASSL
    
    constants.set_test_mode(True)

    aassl = AASSL()
    aassl.setup_system()
    aassl.start_system()
