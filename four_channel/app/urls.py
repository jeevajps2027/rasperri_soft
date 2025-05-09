from django.conf import settings
from django.urls import path,include
from django.conf.urls.static import static
from .views import measurement,master,parameter,spc,changed_name,report_xlsx,report_pdf,report,measurement_count,spc_download
from .views import comport,login,data,measure_data,backup,delete_measure_data,spcCharts,get_parameters,get_parameter_value


urlpatterns = [
    path('',login,name="login"),
    path('measurement/',measurement,name="measurement"),
    path('master/',master,name="master"),
    path('parameter/',parameter,name="parameter"),
    path('report/',report,name="report"),
    path('comport/',comport,name="comport"),
    path('data/',data,name="data"),
    path('measure_data/',measure_data,name="measure_data"),
    path('delete_measure_data/',delete_measure_data,name="delete_measure_data"),
    path('measurement_count/',measurement_count,name="measurement_count"),
    path('report_xlsx/',report_xlsx,name="report_xlsx"),
    path('report_pdf/',report_pdf,name="report_pdf"),
    path('spc/',spc,name="spc"),
    path('spcCharts/',spcCharts,name="spcCharts"),
    path('changed_name/',changed_name,name="changed_name"),
    path('backup/', backup, name='backup'),
    path('get_parameters/',get_parameters,name='get_parameters'),
    path('get_parameter_value/',get_parameter_value,name='get_parameter_value'),
    path('spc_download/',spc_download,name='spc_download'),

    
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)