import unittest
from unittest.mock import Mock, patch, call
from plant import Plant, Status, State
from adafruit_mcp3xxx.analog_in import AnalogIn
from datetime import datetime

class TestPlant(unittest.TestCase):
    def setUp(self):
        self.plant = Plant("TestPlant", 0, 100, 40, 80)

    @patch('plant.AnalogIn')
    def test_calculate_moisture_saturated(self, mock_analog_in):
        mock_channel = Mock(spec=AnalogIn)
        mock_analog_in.return_value = mock_channel
        mock_channel.voltage = 1.3

        moisture = self.plant.calculate_moisture()
        self.assertEqual(moisture, 100)
        
    @patch('plant.AnalogIn')
    def test_calculate_moisture_dry(self, mock_analog_in):
        mock_channel = Mock(spec=AnalogIn)
        mock_channel.voltage = 2.85
        mock_analog_in.return_value = mock_channel

        moisture = self.plant.calculate_moisture()
        self.assertEqual(moisture, 0)

    @patch('builtins.open', create=True)
    @patch('plant.datetime')
    @patch('plant.AnalogIn')
    def test_log_moisture_change(self, mock_analog_in, mock_datetime, mock_open):
        mock_channel = Mock(spec=AnalogIn)
        mock_channel.voltage = 2.0
        mock_analog_in.return_value = mock_channel

        mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 1, 0)
        self.plant.previous_voltage = 2.1

        self.plant.log_moisture_change()

        mock_open.assert_called_with('/home/zuldijin/Desktop/plant_TestPlant.log', 'a+')
        mock_open.return_value.write.assert_called_with(
            f"{datetime.now()}\tPlant: TestPlant\tStatus: Reading, for: 1 minutes\tADC Voltage: 2.0V\tMoisture: 100%\n"
        )
        self.assertTrue(self.plant.previous_voltage == self.plant.channel.voltage)

    @patch('plant.time.sleep')
    @patch('builtins.print')
    def test_irrigate(self, mock_print, mock_sleep):
        self.plant.status.state = State.Absorbing

        with patch.object(self.plant.status, 'get_time_elapsed', return_value=4):
            self.plant.irrigate()

        mock_sleep.assert_not_called()
        mock_print.assert_called_with("Irrigating for 4 seconds")

    @patch('plant.pigpio.pi')
    @patch('plant.time.sleep')
    def test_wait(self, mock_sleep, mock_pigpio):
        self.plant.wait()
        mock_pigpio.return_value.write.assert_called_with(16, True)
        mock_sleep.assert_called_with(1)
        mock_pigpio.return_value.write.assert_called_with(16, False)
        mock_sleep.assert_called_with(1)

    @patch('builtins.print')
    def test_run(self, mock_print):
        self.plant.run()
        mock_print.assert_called()

class TestStatus(unittest.TestCase):
    def test_has_changed(self):
        status = Status()
        status.state = State.Absorbing
        status.previous_state = State.Reading
        self.assertTrue(status.has_changed())

    def test_change_status(self):
        status = Status()
        status.change_status(State.Irrigating)
        self.assertEqual(status.state, State.Irrigating)
        self.assertEqual(status.previous_state, State.Reading)

    @patch('plant.datetime')
    def test_get_time_elapsed(self, mock_datetime):
        status = Status()
        status.time = datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 2, 0)
        elapsed_time = status.get_time_elapsed()
        self.assertEqual(elapsed_time, 2)

if __name__ == '__main__':
    unittest.main()