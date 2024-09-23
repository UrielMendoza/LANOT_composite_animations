'''
create_animation_cloud.py

Este script crea una amicacion con datos de compuestos especificos RGB de GOES 16, para mostrar la evolucion temporal de los productos.

@autor: urielm
@date: 2024-09-23
'''

# Importamos las librerias necesarias
import os
from glob import glob
import datetime

# Se definen las carpetas de trabajo
pathInput = '/datawork/fires_data/bandas_productos_y_compuestos_goes16_conus/08_compuestos_geo_mex'
pathOutput = '/datawork/datawork_tmp/LANOT_animacion_nubes/output'
pathTmp = '/datawork/datawork_tmp/LANOT_animacion_nubes/tmp'

compisite = 'DayLandCloudFire'

dirs_years = glob(f'{pathInput}/'+compisite+'/*')

for year in dirs_years:
    year_str = year.split('/')[-1]
    dirs_days = glob(f'{year}/*')
    for day in dirs_days:
        files = glob(f'{day}/*')
        list_hours = []
        for file in files:
            # Obtiene los datos del archivo
            name_file = file.split('/')[-1]
            # Fecha del arcvhivo OR_ABI-L2-MCMIPC-M3_G16_s20181231_1652CDMX_s20181231_2252UTC_DayLandCloudFire_Mex_Geo.tif, obtiene el de CDMX
            date = name_file.split('_')[3]
            hour = name_file.split('_')[4]
            # Trasforma a formato de fecha
            date = datetime.datetime.strptime(date, 's%Y%m%d')
            hour = datetime.datetime.strptime(hour, '%H%MCDMX')
            # Agrega a la lista el primer archivo de las 11am, 1pm y 3pm
            if hour.hour in [11, 13, 15]:
                list_hours.append(file)
        # Ordena la lista
        list_hours.sort()
        # Reproyecta a EPSG:6372 y los guarda en una carpeta temporal con el mismo nombre del archivo original solo en vez de _Geo a _conica
        for hour in list_hours:
            name_file = hour.split('/')[-1]
            name_file_conica = name_file.replace('Geo', 'conica')
            os.system(f'gdalwarp -t_srs EPSG:6372 {hour}/{name_file} {pathTmp}/{name_file_conica}')
        # Pasa la tres imagenes a un png y los guarda igual en la carpeta temporal
        os.system(f'convert -delay 100 {pathTmp}/*conica.tif {pathTmp}/animation_{date}.gif')
    # Une las imagenes en una sola animacion por año, solo con las png, en formato mp4 con ffmpeg, le agrega el sensor GOES16_ABI mas el compuesto y el año
    # Crea primero la carpeta del año si no existe
    if not os.path.exists(f'{pathOutput}/{compisite}'):
        os.makedirs(f'{pathOutput}/{compisite}/{year_str}')
    os.system(f'ffmpeg -r 3 -i {pathTmp}/animation_%Y%m%d.gif -vf "fps=3,format=yuv420p" {pathOutput}/{compisite}/{year_str}/' + 'GOES16_ABI_' + compisite + '_' + year_str + '.mp4')

    # Elimina los archivos temporales
    os.system(f'rm -rf {pathTmp}/*')
    
    

    






