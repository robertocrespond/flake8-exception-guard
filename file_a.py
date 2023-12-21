from file_b import b

def a():
    result_b = b()
    return f"Function a calling function b: {result_b}"

if __name__ == "__main__":
    print(a())