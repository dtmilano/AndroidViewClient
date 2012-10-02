:

export ANDROID_HOME=/Users/diego/opt/android-sdk
export ANDROID_VIEW_CLIENT_HOME=/Users/diego/AndroidViewClient/AndroidViewClient
# setting PYTHONPATH also works
#export PYTHONPATH=$PYTHONPATH:/Users/diego/AndroidViewClient/AndroidViewClient


add_to_path ()
{
    if [[ "$PATH" =~ (^|:)"${1}"(:|$) ]]
    then
        return 0
    fi
    export PATH=${1}:$PATH
}


add_to_path $ANDROID_HOME/tools
add_to_path $ANDROID_HOME/platform-tools
