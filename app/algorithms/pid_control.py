import datetime
import numpy
from app.algorithms import Algorithm


class PIDLoopHunting(Algorithm):

    def __init__(self):
        self.set_name_desc()
        self.set_format()
        self.set_min_period()
        self.set_control_variable()
        self.set_freq_cutoff()

    def set_name_desc(self):
        self.name = "PID control loop hunting"
        self.description = "PID control loop hunting"

    def set_format(self):
        self.format = "bool"

    def set_min_period(self):
        self.min_period = 1/60.0

    def set_control_variable(self):
        self.control_variable = None

    def set_freq_cutoff(self):
        # this is the tuning parameter
        self.freq_cutoff = 100

    def run(self, data):
        # using units of minutes in this algorithm
        # only check for oscilations with a period of less than 60 minutes
        min_period = 1/60.0
        freq_sums = {}

        for hours in range(24, 1, -1):
            # grab an hour of data
            samples = data.time_range(self.control_variable, datetime.timedelta(hours=hours), datetime.timedelta(hours=hours-1))
            # FFT needs evenly spaced samples to work. Resample to 1 minute rather than 1 second because computationally expensive - gives max resolution of 1 oscillation per 2 minutes
            # up (interpolate) and downsample (first) since the sample rate is unknown and variable. assuming a COV trend here
            samples_mins = samples.resample('1Min').first().interpolate(method='quadratic')

            N = len(samples_mins)
            if N > 0:
                # perform fft
                x_fft = numpy.linspace(0, 1, N)
                samples_fft = fft(samples_mins)

                i = numpy.argmax(x_fft > min_period)
                # we only care about oscillations faster than our min period. Also only take half the range since the FFT is mirrored, avoid doubling up
                sum_range = samples_fft[i:int(N/2)]

                # metric to judge overall instability, sum of high frequencies
                freq_sums[hours] = sum(numpy.abs(sum_range))
            else:
                freq_sums[hours] = 0

        result = max(freq_sums) > self.freq_cutoff
        passed = not result

        return [result, passed]


# check if chilled water valve actuator is hunting.
# in this algorithm, we are checking the fourier transform for signs of an oscillating signal.
# the idea is that an unstable pid loop will show up as a magnitude in the high frequency range (e.g more than 1 oscillation per hour).
# we transform the data to the right format (i.e. interval data), perform a fft, ignore all the low frequency oscillations, then add up what's left.
# if the sum of the high frequencies is large, then there's some oscillation going on. use a tuning parameter to decide how large is 'too large'
class ChwValveHunting(PIDLoopHunting):

    def set_name_desc(self):
        self.name = "chilled water valve actuator hunting"
        self.description = "chilled water valve actuator hunting"

    def set_format(self):
        self.format = "bool"

    def set_min_period(self):
        self.min_period = 1/60.0

    def set_control_variable(self):
        self.control_variable = None

    def set_freq_cutoff(self):
        # this is the tuning parameter
        self.freq_cutoff = 100
