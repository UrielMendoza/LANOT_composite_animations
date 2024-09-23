'''
create_animation_cloud.py

Este script crea una animacion con datos de compuestos especificos RGB de GOES 16, para mostrar la evolucion temporal de los productos.

@autor: urielm
@date: 2024-09-23
'''

import os
from glob import glob
import datetime
from PIL import Image


def create_output_directories(pathTmp, year_str, pathOutput, compisite):
    year_tmp_folder = f'{pathTmp}/{year_str}'
    if not os.path.exists(year_tmp_folder):
        os.makedirs(year_tmp_folder)
    
    output_folder = f'{pathOutput}/{compisite}/{year_str}'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    return year_tmp_folder, output_folder


def convert_tiff_to_png(tiff_file, png_file):
    try:
        # Abre el archivo TIFF y lo convierte a RGB
        with Image.open(tiff_file) as img:
            img = img.convert("RGB")  # Asegurarse de que esté en modo RGB
            img.save(png_file, "PNG")  # Guardar la imagen como PNG
            print(f"Convertido TIFF a PNG: {png_file}")
    except Exception as e:
        print(f"Error al convertir TIFF a PNG: {e}")


def process_images(list_hours, year_tmp_folder, font_path, font_size, font_color, compisite):
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

        # Convertir TIFF a PNG usando Pillow
        convert_tiff_to_png(tiff_reprojected, png_file)

        # Eliminar archivo .tif después de la conversión
        if os.path.exists(tiff_reprojected):
            os.remove(tiff_reprojected)
        
        # Añadir textos a la imagen PNG usando ffmpeg
        annotated_png = f'{year_tmp_folder}/annotated_{name_file_conica.replace("tif", "png")}'
        date_obj = datetime.datetime.strptime(name_file.split('_')[3], 's%Y%m%d')
        hour_obj = datetime.datetime.strptime(name_file.split('_')[4], '%H%MCDMX')
        date_text = date_obj.strftime("%Y-%m-%d")
        time_text = hour_obj.strftime("%H:%M")
        
        # Añadir "GOES-16 ABI {compisite}" primero y luego la fecha y hora abajo, con GMT-6
        try:
            os.system(f'ffmpeg -i {png_file} -vf "drawtext=text=\'GOES-16 ABI {compisite}\':fontfile={font_path}:'
                      f'fontsize={font_size}:fontcolor={font_color}:x=10:y=h-th-50, '
                      f'drawtext=text=\'{date_text} {time_text} GMT-6\':fontfile={font_path}:'
                      f'fontsize={font_size}:fontcolor={font_color}:x=10:y=h-th-10" -y {annotated_png}')
        except Exception as e:
            print(f'Error añadiendo texto con ffmpeg al archivo {png_file}: {e}')
    
    return glob(f'{year_tmp_folder}/annotated_*.png')


def create_animation(list_files, year_str, output_folder, compisite, framerate, outfps, scale):
    if list_files:
        i = 1
        for file in list_files:
            os.rename(file, f'{os.path.dirname(file)}/s{year_str}_{str(i).zfill(4)}.png')
            i += 1

        # Crear animación con ffmpeg usando los parámetros proporcionados
        try:
            os.system(f'ffmpeg -framerate {framerate} -pattern_type glob -i "{os.path.dirname(list_files[0])}/s{year_str}_%04d.png" '
                      f'-vcodec libx264 -r {outfps} -pix_fmt yuv420p -profile:v baseline -level 3 '
                      f'-vf "scale=-2:{scale}" -crf 30 -y {output_folder}/GOES16_ABI_{compisite}_{year_str}.mp4')
        except Exception as e:
            print(f'Error creando animación para {year_str}: {e}')


def process_year(year, pathTmp, pathOutput, font_path, font_size, font_color, framerate, outfps, scale, compisite):
    print('Procesando año:', year)
    year_str = year.split('/')[-1]
    
    # Crear las carpetas necesarias
    year_tmp_folder, output_folder = create_output_directories(pathTmp, year_str, pathOutput, compisite)
    
    dirs_days = glob(f'{year}/*')
    print('Numero de dias a procesar:', len(dirs_days))
    
    for day in dirs_days:
        print('Procesando dia:', day)
        files = glob(f'{day}/*')
        list_hours = []
        selected_hours = {11: False, 13: False, 15: False}  # Para verificar si ya seleccionamos una imagen para cada hora

        for file in files:
            name_file = file.split('/')[-1]
            date = name_file.split('_')[3]
            hour = name_file.split('_')[4]
            hour_obj = datetime.datetime.strptime(hour, '%H%MCDMX')

            # Selecciona la primera imagen de cada hora (11, 13, 15) y sigue con la siguiente
            if hour_obj.hour == 11 and not selected_hours[11]:
                list_hours.append(file)
                selected_hours[11] = True  # Marca que ya se seleccionó una imagen de las 11
            elif hour_obj.hour == 13 and not selected_hours[13]:
                list_hours.append(file)
                selected_hours[13] = True  # Marca que ya se seleccionó una imagen de las 13
            elif hour_obj.hour == 15 and not selected_hours[15]:
                list_hours.append(file)
                selected_hours[15] = True  # Marca que ya se seleccionó una imagen de las 15

            # Si ya hemos seleccionado una imagen de cada hora (11, 13 y 15), paramos
            if all(selected_hours.values()):
                break

        list_hours.sort()
        print('Archivos seleccionados para procesar:', len(list_hours))

        # Procesar imágenes
        list_files = process_images(list_hours, year_tmp_folder, font_path, font_size, font_color, compisite)
    
        # Crear animación para este año
        create_animation(list_files, year_str, output_folder, compisite, framerate, outfps, scale)


def main(pathInput, pathOutput, pathTmp, framerate, outfps, scale, font_size, font_color, font_path, compisite='DayLandCloudFire'):
    dirs_years = glob(f'{pathInput}/{compisite}/*')

    for year in dirs_years:
        process_year(year, pathTmp, pathOutput, font_path, font_size, font_color, framerate, outfps, scale, compisite)


if __name__ == "__main__":
    # Parámetros configurables
    pathInput = '/datawork/fires_data/bandas_productos_y_compuestos_goes16_conus/08_compuestos_geo_mex'
    pathOutput = '/datawork/datawork_tmp/LANOT_animacion_nubes/output'
    pathTmp = '/datawork/datawork_tmp/LANOT_animacion_nubes/tmp'
    
    framerate = 1  # Frames por segundo
    outfps = 10  # Frames por segundo de salida para el video
    scale = 720  # Escala de salida para las imágenes (altura)
    font_size = 24  # Tamaño de la fuente para los textos en las imágenes
    font_color = "white"  # Color del texto
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Ruta de la fuente para el texto
    
    # Ejecutar el script principal
    main(pathInput, pathOutput, pathTmp, framerate, outfps, scale, font_size, font_color, font_path)