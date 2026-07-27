from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter


def mini_sales_chart(data: list[tuple[str, float]], title: str = "Sales Trend") -> QChartView:
    series = QBarSeries()
    bar_set = QBarSet("Amount")
    bar_set.setColor(QColor("#3498db"))
    for _, val in data:
        bar_set.append(val)
    series.append(bar_set)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
    chart.legend().setVisible(False)
    chart.setBackgroundVisible(False)
    chart.setMargins((0, 0, 0, 0))

    categories = [label for label, _ in data]
    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    axis_x.setLabelsAngle(-45)
    axis_x.setLabelsFont(axis_x.labelsFont())
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    axis_y.setTitleText("₹")
    axis_y.setLabelsFont(axis_y.labelsFont())
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_y)

    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setMinimumHeight(200)
    return view
