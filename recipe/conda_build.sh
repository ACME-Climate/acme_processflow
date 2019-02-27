export VERSION="2.2.0"
export BUILD_NAME="alpha3"
export CONDA_BLD_PATH=~/conda-bld
USER="e3sm"
#PLATFORM="linux-64"
#PLATFORM="noarch"
PLATFORM="osx"
PKG="processflow"

if [ -d $CONDA_BLD_PATH ]; then
    rm -rf $CONDA_BLD_PATH
fi
echo "Creating build dir at" $CONDA_BLD_PATH
mkdir $CONDA_BLD_PATH

conda config --set anaconda_upload no
if [ ! -z "$1" ]; then
    export TAG="$1"
else
    export TAG="master"
fi
echo "Building" $VERSION"-"$BUILD_NAME "for label:" $TAG

conda build -c $USER -c conda-forge -c cdat .

if [ $? -eq 1 ]; then
    echo "conda build failed"
    exit
fi

if [ ! -z "$1" ]; then
    anaconda upload -u $USER -l "$1" $CONDA_BLD_PATH/$PLATFORM/$PKG-$VERSION-$BUILD_NAME.tar.bz2 
else
    anaconda upload -u $USER $CONDA_BLD_PATH/$PLATFORM/$PKG-$VERSION-$BUILD_NAME.tar.bz2
fi
