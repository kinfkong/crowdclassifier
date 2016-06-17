### Setup Python Virtual Environment
Make sure Python 2.7 and virtualenv are installed. 

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

### Load Training Data to Haven OnDemand
Open the [create-text-index](https://dev.havenondemand.com/apis/createtextindex#try) api page, and create an index with standard flavor. 
No need to set the optional attributes.

Edit the following values in `conf/config.json` file:
* textIndex - the name of the index you just created
* apiKey - your api key

Then execute the following command to add training data to the created index:
```sh
python load_data.py data/spreadsheet.xlsx
```

Where `data/spreadsheet.xlsx` is the spreadsheet file containing the training data, you can replace it with yours as long as it follows the same format.

This script will call the [add-to-text-index](https://dev.havenondemand.com/apis/addtotextindex#overview) api to insert the training data.

### Run REST Server Locally
The REST app script will use the `textIndex` and `apiKey` values in the `conf/config.json` file, make sure they are correct. 

Run the following command to start the REST server:
```sh
python app.py
```
Then you will be able to access the api at: `http://localhost:5000/api/v1/categorize`. 

When the REST api is called, it will call the [find-similar](https://dev.havenondemand.com/apis/findsimilar#overview) api to get the matched documents and return the category values.

### Deployed Heroku App
Please use the url below to test:
```
https://whispering-crag-71725.herokuapp.com/api/v1/categorize
```

### Verification
Load the `doc/HPE.postman_collection.json` file in your postman, it contains a test to post data to the deployed Heroku app api endpoint above. 
Send the request, and you will receive the categorized response. 