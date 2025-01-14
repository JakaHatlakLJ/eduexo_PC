import time
from datetime import datetime

from pylsl import StreamInlet, resolve_byprop

class LSLPredictionReporter:
    """
    A template class that:
      1. Resolves an LSL stream by name (or other property),
      2. Continuously reads samples (predictions),
      3. Logs them in memory and prints them (optional).

    Usage:
        reporter = LSLPredictionReporter(stream_name='MyPredictionsStream')
        reporter.start_reporting()
        # Press Ctrl+C or kill the process to stop
    """

    def __init__(
        self,
        stream_name: str = "MyPredictionsStream",
        max_samples: int = 0,
        poll_interval: float = 0.01,
        verbose: bool = True
    ):
        """
        :param stream_name: The name of the LSL stream to connect to.
        :param max_samples: If > 0, stop after collecting this many samples; otherwise run until manually stopped.
        :param poll_interval: Sleep time (in seconds) between reads if no samples are available.
        :param verbose: If True, prints predictions to console as they arrive.
        """
        self.stream_name = stream_name
        self.max_samples = max_samples
        self.poll_interval = poll_interval
        self.verbose = verbose

        self._stop = False
        self._inlet = None
        self._samples_collected = 0

        # A list to store (system_time, lsl_timestamp, prediction_value)
        self.prediction_log = []

    def _resolve_stream(self):
        """
        Resolve the LSL stream by name. Raises an exception if no stream is found.
        """
        print(f"Resolving LSL stream by name: '{self.stream_name}' ...")
        streams = resolve_byprop('name', self.stream_name, timeout=5)
        if not streams:
            raise RuntimeError(f"No LSL stream found with name: '{self.stream_name}'")
        # If multiple streams share the same name, pick the first
        return streams[0]

    def start_reporting(self):
        """
        Main entry point to start reading predictions from the LSL stream.
        """
        try:
            stream_info = self._resolve_stream()
            self._inlet = StreamInlet(stream_info)
            print(f"Connected to stream: {self.stream_name}")

            print("Starting to report predictions (Press Ctrl+C to stop)...")
            while not self._stop:
                # Try to pull a sample (non-blocking or short timeout)
                sample, lsl_timestamp = self._inlet.pull_sample(timeout=0.1)
                if sample is not None and len(sample) > 0:
                    system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    prediction_value = sample[0]  # If there's only 1 channel

                    # Store in our list
                    self.prediction_log.append((system_time, lsl_timestamp, prediction_value))
                    self._samples_collected += 1

                    # Optionally print it
                    if self.verbose:
                        print(
                            f"[LSL PREDICTION] SystemTime={system_time}, "
                            f"LSLTime={lsl_timestamp:.3f}, Pred={prediction_value}"
                        )

                    # Check if we reached max_samples
                    if self.max_samples > 0 and self._samples_collected >= self.max_samples:
                        print(f"Reached max_samples={self.max_samples}. Stopping.")
                        break
                else:
                    # No sample available; sleep briefly
                    time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("Keyboard interrupt received. Stopping reporting.")
        except Exception as e:
            print(f"Error in LSLPredictionReporter: {e}")
        finally:
            self.stop_reporting()

    def stop_reporting(self):
        """
        Stop receiving data gracefully.
        """
        self._stop = True
        print("LSLPredictionReporter stopped.")

    def generate_report(self) -> str:
        """
        Create a simple text-based report of all collected predictions.
        Returns the report as a string. You can adapt how the data is formatted.
        """
        lines = []
        lines.append("==== PREDICTION REPORT ====")
        for i, (system_time, lsl_time, pred) in enumerate(self.prediction_log, start=1):
            lines.append(
                f"{i:04d}: [SystemTime={system_time}] "
                f"[LSLTime={lsl_time:.3f}] Prediction={pred}"
            )
        lines.append("==== END OF REPORT ====")
        return "\n".join(lines)

    def __del__(self):
        # Cleanup in case user forgets to call stop_reporting()
        self.stop_reporting()


if __name__ == "__main__":
    # Example usage
    reporter = LSLPredictionReporter(
        stream_name="MyPredictionsStream",
        max_samples=0,   # 0 means run until manually stopped
        poll_interval=0.01,
        verbose=True
    )
    reporter.start_reporting()

    # If you want to do something after it stops:
    # report_text = reporter.generate_report()
    # print(report_text)
