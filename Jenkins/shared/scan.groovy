def call(image) {

    sh """

    echo "Running Trivy Scan..."

    trivy image \
        --severity HIGH,CRITICAL \
        --exit-code 0 \
        ${image}

    """

}