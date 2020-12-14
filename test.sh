rm -v diretório/mir*
tar xvzf arquivos.tgz
./mir.py -@ instruc.lst diretório/
touch diretório/arq0.txt
rm diretório/arq1.txt
./mir.py -A diretório/
