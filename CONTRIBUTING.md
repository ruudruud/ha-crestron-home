# Contributing to Crestron Home Integration

Thank you for considering contributing to the Crestron Home integration for Home Assistant!

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b my-new-feature`
3. Make your changes
4. Run the linting tools: `ruff check .`
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin my-new-feature`
7. Submit a pull request

## Development Environment

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```
4. (Optional) Set up a test Home Assistant instance for development:
   ```bash
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install Home Assistant
   pip install homeassistant
   
   # Create a configuration directory
   mkdir config
   
   # Run Home Assistant
   hass -c config
   ```

## Code Style

This project follows the Home Assistant code style guidelines:

- Use double quotes for strings
- Use 4 spaces for indentation
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values

The project uses pre-commit hooks to enforce code style. You can run the checks manually:

```bash
pre-commit run --all-files
```

## Testing

Before submitting a pull request, please test your changes:

1. Install the integration in a test Home Assistant instance
   - Copy the `custom_components/crestron_home` directory to your Home Assistant `custom_components` directory
   - Restart Home Assistant
   - Add the integration through the UI

2. Verify that your changes work as expected
   - Test all affected functionality
   - Ensure that the integration works with different Crestron Home configurations

3. Ensure that existing functionality is not broken
   - Test with different device types
   - Verify that all entities are created correctly
   - Check that all controls work as expected

4. Use the crestron_debug.py script to verify communication with your Crestron Home system (see [Using crestron_debug.py](#using-crestron_debugpy))

## Using crestron_debug.py

The `crestron_debug.py` script is a powerful tool for debugging and testing your Crestron Home system integration. It allows you to directly interact with the Crestron Home API without going through Home Assistant.

### Setup

1. Create a `.env` file in the same directory as `crestron_debug.py` with your Crestron Home system details:
   ```
   HOST=your-crestron-home-ip
   TOKEN=your-crestron-home-token
   ```

2. Alternatively, you can provide these details as command-line arguments.

### Basic Usage

Run the script with Python 3:

```bash
python crestron_debug.py
```

This will connect to your Crestron Home system and display all lights.

### Command-line Options

The script supports several options to customize its behavior:

- `--host HOST`: Hostname or IP address of the Crestron Home system (overrides .env)
- `--token TOKEN`: Authentication token for the Crestron Home system (overrides .env)
- `--room ROOM`: Filter devices by room name
- `--sort {name,room,status,level}`: Sort devices by the specified field (default: room)
- `--all`: Show all devices, not just lights
- `--sensors`: Show only sensors (occupancy, door, photo)
- `--raw`: Show raw API data instead of formatted output
- `--help`: Show help message and exit

### Examples

1. View all lights in a specific room:
   ```bash
   python crestron_debug.py --room "Living Room"
   ```

2. View all devices sorted by status:
   ```bash
   python crestron_debug.py --all --sort status
   ```

3. View raw API data for a specific room:
   ```bash
   python crestron_debug.py --room "Kitchen" --raw
   ```

4. View only sensors in a specific room:
   ```bash
   python crestron_debug.py --sensors --room "Bedroom"
   ```

### Debugging with crestron_debug.py

The script is particularly useful for debugging issues with your Crestron Home integration:

1. **Connection Issues**: Verify that you can connect to your Crestron Home system
   ```bash
   python crestron_debug.py
   ```
   If this fails, check your network connection, IP address, and authentication token.

2. **Device Discovery**: Check if specific devices are visible to the API
   ```bash
   python crestron_debug.py --all
   ```
   This helps verify that devices are properly configured in your Crestron Home system.

3. **API Response Analysis**: Examine the raw API responses
   ```bash
   python crestron_debug.py --room "Living Room" --raw
   ```
   This is useful for understanding the data structure and troubleshooting issues with specific devices.

4. **Sensor Status**: Check the status of sensors
   ```bash
   python crestron_debug.py --sensors
   ```
   This helps verify that sensors are reporting correctly.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub:

1. Use a clear and descriptive title
2. Provide a detailed description of the issue or feature request
3. Include steps to reproduce the issue (for bugs)
4. Include your Home Assistant and Crestron Home versions
5. Attach logs if applicable

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
