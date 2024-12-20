import numpy as np

class SPIWaveformGenerator:
    def __init__(self, sck_frequency, amplitude, t_start, initial_gap, num_clock_pulses, mosi_data):
        self.sck_frequency = sck_frequency  # SCK frequency in Hz
        self.amplitude = amplitude  # Voltage amplitude
        self.t_start = t_start  # Start time
        self.initial_gap = initial_gap  # Initial gap (high state)
        self.num_clock_pulses = num_clock_pulses  # Number of SCK clock pulses
        self.mosi_data = mosi_data  # MOSI data as a list of bits (e.g., [0, 1, 0, 1])

        # Initialize time parameters
        self.refresh_param()

        # Clear output files
        with open("sck_wave.txt", "w"), open("cs_wave.txt", "w"), open("mosi_wave.txt", "w"):
            pass

    def refresh_param(self):
        """
        Recalculate timing parameters based on current start time and SCK frequency.
        """
        self.bit_duration = 1 / self.sck_frequency  # Duration of one clock pulse
        self.active_duration = self.num_clock_pulses * self.bit_duration  # Duration of all SCK pulses
        self.time_step = 1 / (1000 * self.sck_frequency)  # Default time resolution
        self.t_final = self.t_start + self.initial_gap + self.active_duration + self.bit_duration  # End time
        self.time_points = np.arange(self.t_start, self.t_final, self.time_step)  # Time points array

    def generate_sck_wave(self):
        sck_wave = np.ones_like(self.time_points) * self.amplitude  # Default high state
        for i, t in enumerate(self.time_points):
            if self.initial_gap <= t - self.t_start < self.initial_gap + self.active_duration:
                pulse_time = (t - self.t_start - self.initial_gap) % self.bit_duration
                sck_wave[i] = 0 if pulse_time < (self.bit_duration / 2) else self.amplitude
        return sck_wave

    def generate_cs_wave(self):
        cs_wave = np.ones_like(self.time_points) * self.amplitude  # Default high state
        cs_wave[(self.time_points >= self.t_start + self.initial_gap) &
                (self.time_points < self.t_start + self.initial_gap + self.active_duration)] = 0
        return cs_wave

    def generate_mosi_wave(self):
        mosi_wave = np.ones_like(self.time_points) * self.amplitude  # Default high state
        for i, bit in enumerate(self.mosi_data):
            start_time = self.t_start + self.initial_gap + i * self.bit_duration
            end_time = start_time + self.bit_duration
            mosi_wave[
                (self.time_points >= start_time) & (self.time_points < end_time)] = 0 if bit == 0 else self.amplitude
        return mosi_wave

    def save_waveform(self, filename, wave):
        with open(filename, "a") as file:
            v_hist = wave[0]
            idx_count = 0
            for t, v in zip(self.time_points, wave):
                t_ms = t * 1e3  # Convert time to milliseconds
                if v != v_hist:
                    # Write the previous voltage change point
                    prev_t_ms = self.time_points[idx_count - 1] * 1e3
                    file.write(f"{prev_t_ms:.9f}m\t{wave[idx_count - 1]:.6e}\n")
                    # Write the current voltage change point
                    file.write(f"{t_ms:.9f}m\t{v:.6e}\n")
                    v_hist = v
                idx_count += 1

            # Write the final point
            final_t_ms = self.time_points[idx_count - 1] * 1e3
            file.write(f"{final_t_ms:.6f}m\t{wave[idx_count - 1]:.6e}\n")
    def generate_and_save_all(self):
        # Refresh timing parameters
        self.refresh_param()

        # Generate waveforms
        sck_wave = self.generate_sck_wave()
        cs_wave = self.generate_cs_wave()
        mosi_wave = self.generate_mosi_wave()

        # Save to files
        self.save_waveform("sck_wave.txt", sck_wave)
        self.save_waveform("cs_wave.txt", cs_wave)
        self.save_waveform("mosi_wave.txt", mosi_wave)

        print(f"PWL files updated: 'sck_wave.txt', 'cs_wave.txt', and 'mosi_wave.txt'")



if __name__ == "__main__":
    # Parameters
    sck_frequency = 10 * 1e6  # SCK frequency (10 MHz)
    amplitude = 5  # Amplitude (5V logic)
    t_start = 0  # Start time (0 seconds)
    initial_gap = 1e-6  # Initial gap duration (10 µs)
    num_clock_pulses = 8  # Number of clock pulses
    mosi_data_list = [[0, 1, 0, 1, 1, 0, 1, 0]
                    , [1, 0, 1, 0, 1, 0, 1, 0]
                    , [0, 1, 0, 1, 0, 1, 0, 1]
                    , [0, 1, 1, 0, 0, 1, 1, 0]]  # Initial MOSI data pattern (8 bits)
    # Instantiate generator
    spi_generator = SPIWaveformGenerator(
        sck_frequency=sck_frequency,
        amplitude=amplitude,
        t_start=t_start,
        initial_gap=initial_gap,
        num_clock_pulses=num_clock_pulses,
        mosi_data=[]
    )
    for mosi_data in mosi_data_list:
        spi_generator.mosi_data = mosi_data
        spi_generator.generate_and_save_all()
        spi_generator.t_start = spi_generator.t_final + spi_generator.time_step