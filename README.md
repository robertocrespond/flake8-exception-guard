## flake8_exception_guard

`flake8_exception_guard` is a flake8 plugin that helps you ensure that exceptions are properly handled in your code. It analyzes your Python code and raises alerts if any function calls are not wrapped in exception handling blocks.

### Installation

<!--
You can install `flake8_exception_guard` using pip:

```shell
pip install flake8_exception_guard
``` -->

### Usage

Once installed, you can run `flake8` with the `flake8_exception_guard` plugin enabled:

```shell
flake8 --select FEG
```

This command will analyze your code and raise alerts for any unhandled exceptions.

### Tests

To execute tests, run the following command

```shell
PYTHONPATH=. pytest tests/
```

### Contributing

Contributions to `flake8_exception_guard` are welcome! If you encounter any issues or have suggestions for improvements, please open an issue on the repo.

### License

`flake8_exception_guard` is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
