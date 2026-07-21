def call(status){

    echo "===================================="

    echo "Deployment Status : ${status}"

    echo "Build Number      : ${env.BUILD_NUMBER}"

    echo "Branch            : ${env.BRANCH_NAME}"

    echo "Commit            : ${env.GIT_COMMIT}"

    echo "Author            : ${env.CHANGE_AUTHOR}"

    echo "Job               : ${env.JOB_NAME}"

    echo "Build URL         : ${env.BUILD_URL}"

    echo "===================================="

}