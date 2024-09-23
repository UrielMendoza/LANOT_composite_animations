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
    print('Procesando año:', year)
    year_str = year.split('/')[-1]
    dirs_days = glob(f'{year}/*')
    # Informacion del numero de dias a procesar
    print('Numero de dias a procesar:', len(dirs_days))
    for day in dirs_days:
        print('Procesando dia:', day)
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
        print('Archivos a procesar:', list_hours)
        # Reproyecta a EPSG:6372 y los guarda en una carpeta temporal con el mismo nombre del archivo original solo en vez de _Geo a _conica
        for hour in list_hours:
            name_file = hour.split('/')[-1]
            name_file_conica = name_file.replace('Geo', 'conica')
            os.system(f'gdalwarp -t_srs EPSG:6372 {hour}/{name_file} {pathTmp}/{name_file_conica}')
            # Pasa los tif a png con gdal_translate
            os.system(f'gdal_translate -of PNG {pathTmp}/{name_file_conica} {pathTmp}/{name_file_conica.replace("tif", "png")}')
    # Une las imagenes en una sola animacion por año, solo con las png, en formato mp4 con ffmpeg, le agrega el sensor GOES16_ABI mas el compuesto y el año
    # Crea primero la carpeta del año si no existe
    if not os.path.exists(f'{pathOutput}/{compisite}'):
        os.makedirs(f'{pathOutput}/{compisite}/{year_str}')
    # Renoombra los archivos para que sean numericos
    list_files = glob(f'{pathTmp}/*.png')
    list_files.sort()
    i = 1
    for file in list_files:
        os.rename(file, f'{pathTmp}/s{year_str}_{str(i).zfill(4)}.png')
        i += 1
    # Crea la animacion con ffmpeg
    print('Creando animacion:', f'{pathOutput}/{compisite}/{year_str}/' + 'GOES16_ABI_' + compisite + '_' + year_str + '.mp4')
    os.system(f'ffmpeg -r 1 -i {pathTmp}/s{year_str}_%04d.png -vcodec libx264 -y {pathOutput}/{compisite}/{year_str}/' + 'GOES16_ABI_' + compisite + '_' + year_str + '.mp4')

    # Elimina los archivos temporales
    os.system(f'rm -rf {pathTmp}/*')