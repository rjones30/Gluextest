tag=docker.io/rjones30/gluextest:latest
#docker build --network host --tag $tag .
docker build --no-cache --network host --tag $tag .
if [[ $? == 0 ]]; then
    echo -n "docker build --tag $tag completed successfully, to update the image "
    echo "on dockerhub you need to follow up with the command below."
    echo "$ sudo docker push $tag"
    echo "Then if you want to push the update into a local singularity sandbox, do"
    echo "$ sudo rm -rf out && singularity build --sandbox out docker://registry.hub.docker.com/rjones30/gluex:latest"
else
    echo -n "docker build --tag $tag failed, please fix the problems before you "
    echo "push the updates to dockerhub."
fi
