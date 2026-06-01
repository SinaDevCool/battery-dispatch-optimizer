from dashboard.sections.forecast.comparison import render_forecast_comparison_section
from dashboard.sections.forecast.data_update import render_forecast_data_update_section
from dashboard.sections.forecast.demo import render_forecast_demo_section
from dashboard.sections.forecast.feature_preview import (
    render_forecast_feature_preview_section,
)
from dashboard.sections.forecast.quality import render_forecast_quality_section
from dashboard.sections.forecast.saved_forecast import render_saved_forecast_section
from dashboard.sections.forecast.upload import render_forecast_upload_section


def render_forecast_tab():
    render_forecast_quality_section()
    render_forecast_feature_preview_section()
    render_saved_forecast_section()
    render_forecast_demo_section()
    render_forecast_upload_section()
    render_forecast_comparison_section()
    render_forecast_data_update_section()
