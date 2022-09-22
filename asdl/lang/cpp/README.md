To generate the input used by the demo (preprocessor only):

```bash
clang -x c++ -E -std=c++17 -fPIC -I/usr/include/x86_64-linux-gnu/qt5 -I/usr/include/x86_64-linux-gnu/qt5/QtCore -I/home/gael/Projets/Lima/lima/lima_common/src/ -I/home/gael/Projets/Lima/lima/lima_common/src/common/XMLConfigurationFiles <file>
```

To generate the AST

```bash
clang -x c++ -std=c++17 -fPIC -I/usr/include/x86_64-linux-gnu/qt5 -I/usr/include/x86_64-linux-gnu/qt5/QtCore -I/home/gael/Projets/Lima/lima/lima_common/src/ -I/home/gael/Projets/Lima/lima/lima_common/src/common/XMLConfigurationFiles -Xclang -ast-dump -fsyntax-only <file>
```

To test the AST generator

```bash
python -m pdb demo.py -D -f <file>
```
