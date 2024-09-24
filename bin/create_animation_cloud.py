'''
create_animation_cloud.py

Este script crea una animacion con datos de compuestos especificos RGB de GOES 16, para mostrar la evolucion temporal de los productos.

@autor: urielm
@date: 2024-09-23
'''

import os
from glob import glob
import datetime


def create_output_directories(pathTmp, year_str, pathOutput, compisite):
    year_tmp_folder = f'{pathTmp}/{year_str}'
    if not os.path.exists(year_tmp_folder):
        os.makedirs(year_tmp_folder)
    
    output_folder = f'{pathOutput}/{compisite}/{year_str}'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    return year_tmp_folder, output_folder


def convert_tiff_to_png_gdal(tiff_file, png_file):
    try:
        # Usar gdal_translate para convertir TIFF a PNG, asegurando 8 bits de salida
        os.system(f'gdal_translate -scale 0 255 0 255 -ot Byte -of PNG {tiff_file} {png_file}')
        print(f"Convertido TIFF a PNG con GDAL: {png_file}")
    except Exception as e:
        print(f"Error al convertir TIFF a PNG con GDAL: {e}")


def process_images(list_hours, year_tmp_folder, font_path, font_size, font_color, compisite, logo_path):
    for hour in list_hours:
        name_file = hour.split('/')[-1]
        name_file_conica = name_file.replace('Geo', 'conica')
        png_file = f'{year_tmp_folder}/{name_file_conica.replace("tif", "png")}'
        
        # Si el archivo PNG ya existe, saltar el procesamiento
        if os.path.exists(png_file):
            print(f'El archivo {png_file} ya existe. Saltando procesamiento.')
            continue
        
        # Proyección a EPSG:6372 con gdalwarp
        tiff_reprojected = f'{year_tmp_folder}/{name_file_conica}'
        os.system(f'gdalwarp -t_srs EPSG:6372 {hour} {tiff_reprojected}')

        # Convertir TIFF a PNG usando gdal_translate
        convert_tiff_to_png_gdal(tiff_reprojected, png_file)
        
        # No eliminamos el archivo TIFF aquí, lo hacemos al final del año

        # Añadir textos y logo a la imagen PNG usando ffmpeg
        annotated_png = f'{year_tmp_folder}/annotated_{name_file_conica.replace("tif", "png")}'
        date_obj = datetime.datetime.strptime(name_file.split('_')[3], 's%Y%m%d')
        hour_obj = datetime.datetime.strptime(name_file.split('_')[4], '%H%MCDMX')
        date_text = date_obj.strftime("%Y-%m-%d")
        time_text = hour_obj.strftime("%H:%M")
        
        # Añadir "GOES-16 ABI {compisite}" primero, luego la fecha y hora abajo, con GMT-6 y el logo en la esquina superior derecha
        try:
            os.system(f'ffmpeg -i {png_file} -i {logo_path} -filter_complex "overlay=W-w-10:H-h-10, '
                      f'drawtext=text=\'GOES-16 ABI {compisite}\':fontfile={font_path}:fontsize={font_size}:fontcolor={font_color}:x=10:y=h-th-50, '
                      f'drawtext=text=\'{date_text} {time_text} GMT-6\':fontfile={font_path}:fontsize={font_size}:fontcolor={font_color}:x=10:y=h-th-10" '
                      f'-y {annotated_png}')
        except Exception as e:
            print(f'Error añadiendo texto y logo con ffmpeg al archivo {png_file}: {e}')
    
    return glob(f'{year_tmp_folder}/annotated_*.png')


def create_animation(list_files, year_str, output_folder, compisite, framerate, outfps, scale):
    if list_files:
        i = 1
        for file in list_files:
            new_file = f'{os.path.dirname(file)}/s{year_str}_{str(i).zfill(4)}.png'
            os.rename(file, new_file)
            i += 1

        # Crear animación con ffmpeg usando los parámetros proporcionados
        try:
            png_pattern = f"{os.path.dirname(list_files[0])}/s{year_str}_%04d.png"
            print(f'Generando animación usando los archivos: {png_pattern}')
            os.system(f'ffmpeg -framerate {framerate} -i "{png_pattern}" '
                      f'-vcodec libx264 -r {outfps} -pix_fmt yuv420p -profile:v baseline -level 3 '
                      f'-vf "scale=-2:{scale}" -crf 30 -y {output_folder}/GOES16_ABI_{compisite}_{year_str}.mp4')
        except Exception as e:
            print(f'Error creando animación para {year_str}: {e}')


def delete_tiff_files(year_tmp_folder):
    # Eliminar todos los archivos .tif después de crear la animación
    tiff_files = glob(f'{year_tmp_folder}/*.tif')
    for tiff_file in tiff_files:
        try:
            #os.remove(tiff_file)
            print(f'Archivo TIFF eliminado: {tiff_file}')
        except Exception as e:
            print(f'Error eliminando TIFF: {e}')


def process_year(year, pathTmp, pathOutput, font_path, font_size, font_color, framerate, outfps, scale, compisite, logo_path):
    print('Procesando año:', year)
    year_str = year.split('/')[-1]
    
    # Crear las carpetas necesarias
    year_tmp_folder, output_folder = create_output_directories(pathTmp, year_str, pathOutput, compisite)
    
    # Cambiar la búsqueda de las imágenes por hora usando glob
    print('Buscando imágenes para las 11, 13 y 15 horas')
    hours = {'11': False, '13': False, '15': False}
    list_hours = []
    
    for hour_str in hours.keys():
        # Buscar archivos que contengan la hora específica
        files = glob(f'{year}/*/*_{hour_str}*CDMX*.tif')
        if files:
            list_hours.append(files[0])  # Agregar solo el primer archivo encontrado para esa hora
            print(f'Imagen seleccionada para las {hour_str}: {files[0]}')
    
    print(f'Total de archivos seleccionados para procesar: {len(list_hours)}')

    # Procesar imágenes
    list_files = process_images(list_hours, year_tmp_folder, font_path, font_size, font_color, compisite, logo_path)
    
    # Crear animación para este año
    create_animation(list_files, year_str, output_folder, compisite, framerate, outfps, scale)

    # Eliminar los archivos TIFF después de que se haya creado la animación
    delete_tiff_files(year_tmp_folder)


def main(pathInput, pathOutput, pathTmp, framerate, outfps, scale, font_size, font_color, font_path, logo_path, compisite='DayLandCloudFire'):
    dirs_years = glob(f'{pathInput}/{compisite}/*')

    for year in dirs_years:
        process_year(year, pathTmp, pathOutput, font_path, font_size, font_color, framerate, outfps, scale, compisite, logo_path)


if __name__ == "__main__":
    # Parámetros configurables
    pathInput = '/datawork/fires_data/bandas_productos_y_compuestos_goes16_conus/08_compuestos_geo_mex'
    pathOutput = '/datawork/datawork_tmp/LANOT_animacion_nubes/output'
    pathTmp = '/datawork/datawork_tmp/LANOT_animacion_nubes/tmp'
    logo_path = '/home/urielm/LANOT_composite_animations/img/lanot_logo_b.png'  # Ruta al logo

    framerate = 1  # Frames por segundo
    outfps = 10  # Frames por segundo de salida para el video
    scale = 720  # Escala de salida para las imágenes (altura)
    font_size = 24  # Tamaño de la fuente para los textos en las imágenes
    font_color = "white"  # Color del texto
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Ruta de la fuente para el texto
    
    # Ejecutar el script principal
    main(pathInput, pathOutput, pathTmp, framerate, outfps, scale, font_size, font_color, font_path, logo_path)

