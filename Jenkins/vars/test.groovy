def call() {

    sh """
        echo "Running Unit Tests"

        cd backend

        python -m pip install --upgrade pip

        pip install -r requirements.txt

        pytest
    """

}