




def raises_io_error():






    raise IOError('IOError')





def raises_io_error_and_attribute_error():
    if 4 > 5:
        raise AttributeError('AttributeError')
    raise IOError('IOError')

