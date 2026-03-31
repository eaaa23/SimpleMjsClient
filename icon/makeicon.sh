FILE="src.png";
OUT_DIR="./makeicon.iconset";
OUT_FILE="icon.icns";

mkdir $OUT_DIR;
sips -z 16 16 $FILE --out $OUT_DIR/icon_16x16.png
sips -z 32 32 $FILE --out $OUT_DIR/icon_32x32.png

iconutil -c icns $OUT_DIR -o $OUT_FILE;