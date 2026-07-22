def call(imageName, imageTag) {

    sh """
        echo "Building Docker Image"

        docker build \
        -t ${imageName}:${imageTag} \
        .
    """

}