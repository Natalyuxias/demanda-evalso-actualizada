"""Reproducción completa desde originales, dos procesos como máximo y sin red vial."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import shutil
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(); p.add_argument('--anexos', type=Path, required=True)
    p.add_argument('--salida', type=Path, required=True); args = p.parse_args()
    root, out = args.anexos.resolve(), args.salida.resolve()
    if out.exists(): raise FileExistsError('No sobrescribir: elegir carpeta de ejecución nueva')
    out.mkdir(parents=True); (out/'codigo').mkdir(); (out/'logs').mkdir()
    here = Path(__file__).resolve().parent; revision = here.parent
    names = {'preparar_microdatos.py': revision/'microdatos/preparar_microdatos.py',
             'auditar_aforos_lacustres.py': revision/'aforos/auditar_aforos_lacustres.py',
             'auditar_usuarios.py': revision/'usuarios/auditar_usuarios.py',
             'comparar_07.py': revision/'comparacion/comparar_07.py',
             'consolidar_aristo.py': here/'consolidar_aristo.py',
             'informe_lacustre.py': here/'informe_lacustre.py',
             'reproducir_lacustre.py': here/'reproducir_lacustre.py'}
    for name, src in names.items():
        if not src.exists(): src = here/name  # también permite ejecutar el paquete plano congelado
        shutil.copyfile(src, out/'codigo'/name)
    sources = [root/'Informe ARISTO.pdf', root/'Cap 8/BBDD_para_Pijas_actualizada_EOD_Final.xlsx']
    sources += list((root/'Cap 6/BBDD EOD').glob('*.xlsx')) + list((root/'Cap 6/Mediciones de flujo').glob('*.xlsx'))
    sources += list((root/'demanda_lago_github/outputs/matrices_od_referencia').rglob('*'))
    sources += list((root/'etapa1_terrestre_citra/resultados/cierre_final_04').rglob('*'))
    sources += [root/'demanda_lago_github/scripts/07_matrices_od_referencia.py', root/'demanda_lago_github/data/templates/config_matrices_od.json']
    snapshot = [{'archivo':str(x), 'bytes':x.stat().st_size, 'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sources if x.is_file()]
    (out/'integridad_antes.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2)+'\n')
    commands = []
    def run(name, arguments):
        command = [sys.executable, str(out/'codigo'/name)] + [str(x) for x in arguments]
        commands.append(command)
        with (out/'logs'/(name+'.txt')).open('w') as log:
            subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(run, 'preparar_microdatos.py', ['--anexos',root,'--salida',out/'microdatos/final'])
        d = pool.submit(run, 'comparar_07.py', ['--repo',root/'demanda_lago_github','--salida',out/'comparacion'])
        a.result()
        b = pool.submit(run, 'auditar_aforos_lacustres.py', ['--anexos',root,'--microdatos',out/'microdatos/final/microdatos_ferry_264.csv','--salida',out/'aforos'])
        c = pool.submit(run, 'auditar_usuarios.py', ['--microdatos',out/'microdatos/final/microdatos_ferry_264.csv','--diccionario',root/'Cap 6/BBDD EOD/DiccionarioAPP.xlsx','--informe',root/'Informe ARISTO.pdf','--salida',out/'usuarios'])
        d.result(); b.result(); c.result()
    run('consolidar_aristo.py', ['--anexos',root,'--revision',out,'--salida',out/'resultados/entrega'])
    (out/'comandos_ejecutados.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2)+'\n')
    print(out/'resultados/entrega/informe_lacustre.html')


if __name__ == '__main__': main()
