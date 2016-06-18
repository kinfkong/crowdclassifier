### Setup Python Virtual Environment
Make sure Python 2.7, Python-devel and virtualenv are installed. 

We need SciPy, and it depends on gfortran and BLAS, so,
If you are running in Ubuntu, run:
```sh
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran
```

If you are running in Max OSX, run:
```sh
brew install gfortran 
```


In the submission base directory, execute the the following commands:
```sh
# create virtual env
virtualenv .venv

# activate the virtual env
. .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

The python scripts below should run in this activated virtual env as well.

### Prepare nltk Data
We need nltk for text processing, so download the [nltk data] (http://www.nltk.org/data.html) first:
```sh
python -m nltk.downloader all
```
It will take quite a long time to download and it will occupy about several Gigabytes in disks.
If you did not download the data in default path, you should modify the `nltk_data_path` in `conf/config.json`



### Train the Data

If you desired, you can modify the `trained_models_dir` in `conf/config.json` to change the directory for saving the trained model files.

Train the Palo Alto data: 
```sh
python train.py paloalto ./data/palo_alto_train_data.xlsx
```

Train the chile data:
```sh
python train.py chile ./data/chile_train_data.xlsx
```


### Run REST Server Locally
The REST app script will use the `trained_models_dir` and `nltk_data_path` values in the `conf/config.json` file, make sure they are correct. 

Run the following command to start the REST server:
```sh
python app.py
```


You will be able to access the Palo Alto data api at: `http://localhost:5000/api/v1/categorize/paloalto`;
You will be able to access the chile data api at: `http://localhost:5000/api/v1/categorize/chile`.



### Deployed AWS App
Please use the url below to test:
```
http://52.193.210.43:5000/api/v1/categorize/paloalto
```
and
```
http://52.193.210.43:5000/api/v1/categorize/chile
```

### Verification
Load the `doc/HPE.postman_collection.json` file in your postman, it contains a test to post data to the deployed aws app api endpoint above. 
Send the request, and you will receive the categorized response. 