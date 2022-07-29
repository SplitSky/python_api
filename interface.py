# interface - to connect to the remote API

import json  # Required to pass data
import requests  # Base for REST communications
import datastructure as d  # defined datastructures for communication
import logging

import testing as t  # this import should be removed for deployment

# Connect to logger
log = logging.getLogger()


class API_interface:
    def __init__(self, path_in):
        """Base http path for API"""
        self.path = path_in

    def check_connection(self):
        """Simple test of connectivity against endpoint"""
        return requests.get(self.path) == 200

    def insert_dataset(self, project_name: str, experiment_name: str, dataset_in: d.Dataset):
        """Build a REST request using project name, experiment name etc and insert a dataset"""

        # Try-except for conversion
        try:
            json_payload = dataset_in.convertJSON()
        except BaseException as E:
            raise E

        # Try-except for request
        try:
            response = requests.post(url=self.path + project_name + "/" + experiment_name + "/" + dataset_in.get_name(),
                                     json=json_payload)
        except BaseException as E:
            raise E
        # Log request
        log.info(f"Inserting single dataset- response code: {response}")
        log.info(response.json())
        # Return response code
        return response == 200

    def return_fulldataset(self, project_name: str, experiment_name: str, dataset_name: str):
        response = requests.get(url=self.path + project_name + "/" + experiment_name + "/" + dataset_name)
        print("Retrieving single dataset")
        print("response code: + str(response)")
        print("content of the dataset: ")
        print(response.json())
        temp = response.json()
        temp = json.loads(temp)
        dataset = d.Dataset(name=temp.get("name"), data=temp.get("data"), meta=temp.get("meta"),
                            data_type=temp.get("data_type"))
        return dataset  # returns an object of DataSet class

    def insert_experiment(self, project_name: str, experiment: d.Experiment):
        # takes in the experiment object 
        # perform multiple calls to create an experiment directory and then
        # insert datasets one by one
        experiment_name = experiment.get_name()
        # check if experiment exists:
        if not self.check_experiment_exists(project_name, experiment_name):
            # if it doesn't initialise it
            self.init_experiment(project_name, experiment)

        # init the experiment
        response = []
        temp = experiment.return_datasets()
        for dataset in temp:
            # for each dataset in experiment call API 
            response.append(self.insert_dataset(project_name, experiment_name, dataset))
        # call to initialise experiment and return structure
        return response

    def return_fullexperiment(self, project_name: str, experiment_name: str):
        # call api to find the names of all datasets in the experiment
        print("Printing variables")
        print(self.path)
        print(project_name)
        print(experiment_name)

        response = requests.get(
            self.path + project_name + "/names")  # request the names of the datasets connected to experiment
        print(type(response.json()))
        names_dict = response.json()
        names_list = names_dict.get("names")
        datasets = []
        for name in names_list:
            datasets.append(
                self.return_fulldataset(project_name=project_name, experiment_name=experiment_name, dataset_name=name))
        # call api for each dataset and return the contents -> then add the contents to an object and return the object
        response = requests.get(self.path + project_name + "/" + experiment_name + "/details")
        exp_dict = json.loads(response.json())
        experiment = d.Experiment(name=exp_dict.get("name"), children=datasets, meta=exp_dict.get("meta"))
        return experiment

    def return_fullproject(self, project_name: str):
        response = requests.get(self.path + project_name)
        exp_names_dict = response.json()
        exp_names_list = exp_names_dict.get(self.path + "/names")
        print("Experiment names: ")
        print(exp_names_list)
        experiments = []
        for exp_name in exp_names_list:  # return names function returns type none
            experiments.append(self.return_fullexperiment(project_name, exp_name))

        response = requests.get(self.path + project_name + "/details")
        proj_dict = response.json()
        project = d.Project(name=proj_dict.get("name"), author=proj_dict.get("author"), groups=experiments,
                            meta=proj_dict.get("meta"))
        return project

    def check_project_exists(self, project_name: str):
        response = requests.get(self.path + "names")  # returns a list of strings
        names = response.json().get("names")
        if project_name in names:
            return True
        else:
            print("Project with that name is not present in the database")
            return False

    def check_experiment_exists(self, project_name: str, experiment_name: str):
        response = requests.get(self.path + project_name + "/names")
        names = response.json().get("names")  # may have to json.dumps()

        if experiment_name in names:
            return True
        else:
            print("Experiment with that name is not present in the database")
            return False

    def insert_project(self, project: d.Project):
        response_out = []
        # set project in database
        # check if project exists. If not initialise it 
        if not self.check_project_exists(project_name=project.get_name()):
            self.init_project(project)
        temp = project.return_experiments()
        for experiment in temp:
            response_out.append(self.insert_experiment(project.get_name(), experiment))
        return response_out

    # two functions to return names of the experiment and the names of the project

    def get_project_names(self):
        return requests.get(self.path + "names").json().get("names")

    # initialize project
    def init_project(self, project: d.Project):
        request_body = d.simpleRequestBody(name=project.get_name(), meta=project.get_meta(),
                                           author=project.get_author())
        response = requests.post(self.path + project.get_name() + "/set_project",
                                 json=request_body.convertJSON())  # updates the project variables
        return response

    # initialize experiment
    def init_experiment(self, project_id, experiment: d.Experiment):
        request_body = d.simpleRequestBody(name=experiment.get_name(), meta=experiment.get_meta(), author="a")
        print("request body")
        print(request_body)
        response = requests.post(self.path + project_id + "/" + experiment.get_name() + "/set_experiment",
                                 json=request_body.convertJSON())  # updates the experiment variables
        return response
