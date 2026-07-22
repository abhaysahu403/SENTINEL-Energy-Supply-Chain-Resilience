def call(releaseName, chartPath, imageTag, namespace) {

    sh """

    echo "Deploying Helm Chart..."

    helm upgrade --install ${releaseName} ${chartPath} \
        --namespace ${namespace} \
        --create-namespace \
        --reuse-values \
        --set image.tag=${imageTag}

    """

}