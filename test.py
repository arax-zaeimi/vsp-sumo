import sagaActivityReport
import os
import sys

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    from visualization import plot_summary
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

DEFAULT_TRIPINFO_FILE = 'scenario\output.tripinfo.xml'
DEFAULT_SUMMARY_FILE = 'scenario\output.summary.xml'

# SAGA Report
DEFAULT_REPORT_FILE = 'scenario\\activities_report.json'


def _call_saga_activity_report():
    """ Call directly sagaActivityReport from SUMOActivityGen.. """
    report_options = ['--tripinfo', DEFAULT_TRIPINFO_FILE,
                      '--out', DEFAULT_REPORT_FILE]
    sagaActivityReport.main(report_options)


def _call_plot_summary():
    """ Call directly plot_summary from sumo/tools """
    plot_options = ['-i', DEFAULT_SUMMARY_FILE,
                    '-o', 'summary.png',
                    '--xtime1', '--verbose', '--blind']
    plot_summary.main(plot_options)


if __name__ == "__main__":
    _call_saga_activity_report()
    _call_plot_summary()
