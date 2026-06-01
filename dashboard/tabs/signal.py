from dashboard.sections.signal.action_table import render_signal_action_table_section
from dashboard.sections.signal.control import render_signal_control_section
from dashboard.sections.signal.explanation import render_signal_explanation_section
from dashboard.sections.signal.history import render_signal_history_section
from dashboard.sections.signal.risks import render_signal_risks_section
from dashboard.sections.signal.summary import render_signal_summary_section


def render_signal_tab():
    latest_signal = render_signal_control_section()

    if latest_signal is None:
        return

    signal_data = latest_signal["data"]
    summary = signal_data["summary"]
    dispatch = signal_data["dispatch"]

    render_signal_summary_section(signal_data, summary, dispatch)
    render_signal_action_table_section(dispatch)
    render_signal_explanation_section()
    render_signal_risks_section()
    render_signal_history_section()
