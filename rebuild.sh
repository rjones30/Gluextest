tag=docker.io/rjones30/gluextest:latest
podman build --network host --tag $tag .
#podman build --no-cache --network host --tag $tag .
if [[ $? == 0 ]]; then
    echo -n "podman build --tag $tag completed successfully, to update the image "
    echo "on dockerhub you need to follow up with the command below."
    echo "$ sudo podman push $tag"
    echo "If you get access denied errors, you need to do the following command first."
    echo "$ sudo podman login docker.io/rjones30"
    echo "Then if you want to push the update into a local singularity sandbox, do"
    echo "$ sudo rm -rf out && sudo apptainer build --sandbox out docker://registry.hub.docker.com/rjones30/gluextest:latest"
else
    echo -n "podman build --tag $tag failed, please fix the problems before you "
    echo "push the updates to dockerhub."
fi
