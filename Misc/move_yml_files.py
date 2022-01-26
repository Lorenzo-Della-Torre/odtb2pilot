import os
import shutil
import yaml
import sys

from pprint import pprint



def get_projects():
	walker = os.walk("projects")
	projects = []
	for root, dirs, files in walker:
		projects.append(dirs)
	return projects[0]

def get_files(dir):
	"""Finds all files in "dir" and return their paths

	Args:
		dir (path, string): Where to look for files

	Returns:
		list: List with paths
	"""
	walker = os.walk(dir)
	found_files = []
	found_root = ""
	for root, dirs, files in walker:
		found_root = root
		found_files = files

	if "project_default.yml" in found_files:
		found_files.remove("project_default.yml")

	found_paths = [os.path.join(found_root, file) for file in found_files]

	return found_paths

def list2string(l):
	ret = ""
	for entry in l:
		ret += entry + "\n"

	return ret

def find_existing_file(file_name, directory):
	if "." not in file_name:
		file_name += ".py"
	print("Searching for ", file_name.lower())
	for root, dirs, files in os.walk(directory):
		if file_name.lower() in [file.lower() for file in files]:
			return os.path.join(root)

	return ""

def add_platform_to_yml(platform, yml_file, src_yml = False):
	"""Merged the two yml-files "yml-file" and "src_yml" into "yml-file".
	If "src-yml" is not provided the only thing that will happen is that the key "platform" will
	be added to the "yml-file"

	Args:
		platform (string): The relevant platform
		yml_file (Path, string): Path to yml file that is being merged INTO
		src_yml (bool/Path/string, optional): yml-file the is being merged into "yml-file". Defaults to False.

	Returns:
		boolean: True if merge is successfull
	"""
	dict_with_platform = {}

	input_yml = yml_file
	if src_yml is not False:
		input_yml = src_yml

		with open(yml_file, 'r') as yml_file_stream:
			dict_with_platform = dict_with_platform | yaml.safe_load(yml_file_stream)

	with open(input_yml, 'r') as yml_file_stream:
		input_dict = yaml.safe_load(yml_file_stream)
		dict_with_platform = dict_with_platform | {platform : input_dict}

	with open(yml_file, 'w', ) as yml_file_stream:
		yaml.safe_dump(dict_with_platform, yml_file_stream, indent=8, default_flow_style=False)

	return True



def copy_file(file, destination_file, platform):

	shutil.copy2(file, destination_file)

	return add_platform_to_yml(platform, destination_file)

def move_files(src, platform, dest = "None"):
	"""Move files in src to dest. If dest is false a default destination is used

	Args:
		src (list): list containing paths to the source ymls
		platform (string): platform/project
		dest (string, optional): Where to look for python script matching the yml file. Defaults to "test_test_folder".

	Returns:
		dict: A dictionary containing the yml files that already had a yml file in the destination folder
	"""
	conflict_files = {}
	number_of_moved_files = 0
	yml_with_no_script = []
	for file in src:
		print(f"\n--move file {file}--")

		py_file_to_find = os.path.split(file)[1].split(".")[0]
		dest_folder = find_existing_file(py_file_to_find, dest)
		if dest_folder == "":
			print(f"{file} will not be moved since the script was not found")
			yml_with_no_script.append(file)
			continue

		destination_file = os.path.join(dest_folder, os.path.split(file)[1])
		print("File to move: ", file)
		if os.path.isfile(destination_file):
			conflict_files[file] = destination_file
			print("File already exists {}, will be merged instead".format(destination_file))
			continue

		print("Trying to move to: ", destination_file)
		result = copy_file(file, destination_file, platform)
		if result:
			number_of_moved_files += 1
			print("Moved!")

	return conflict_files, number_of_moved_files, yml_with_no_script

def merge_files(files, selected_project):
	"""Merges all files in the dictionary "files" with existing yml-files.

	Args:
		files (dict): Dictionary containing paths to all yml-files where yml already exists
		selected_project (string): platform/project name
	"""
	number_of_successfull_merges = 0
	for src_file, dest_file in files.items():
		print(f"\n--merge file {src_file}--")
		if add_platform_to_yml(selected_project, dest_file, src_file):
			print("{} and {} successfully merged".format(src_file, dest_file))
			number_of_successfull_merges += 1

	return number_of_successfull_merges


if __name__ == "__main__":

	summary_dict = {}

	projects = get_projects()

	print("--Select project to move. Default is to move all--")
	print(list2string(projects))

	selected_project = input()

	if selected_project == "2":
		print(find_existing_file("e_60017__1_n_as_timeout_non_prog_session_ext", "test_folder"))
		exit()

	src_paths = {}

	try:
		dest_path = sys.argv[1]
	except IndexError:
		dest_path = "test_folder"

	if selected_project not in projects:
		selected_project = "all"
		print("All projects selected")

		for project in projects:
			src_paths[project] = get_files(os.path.join("projects", project, "parameters_yml"))
			summary_dict[project] = {}
			summary_dict[project][f"Number of files found for {project}"] = len(src_paths[project])

	else:
		src_paths[selected_project] = get_files(os.path.join("projects", selected_project, "parameters_yml"))
		summary_dict[selected_project] = {}
		summary_dict[selected_project][f"Number of files found for {selected_project}"] = len(src_paths[selected_project])

	print("--Src files:--")
	pprint(src_paths)

	for project, path in src_paths.items():
		conflict_files, summary_dict[project][f"Number of files moved for {project}"], summary_dict[project][f"files without script {project}"] = move_files(path, project, dest=dest_path)

		summary_dict[project][f"Number of files merged for {project}"] = 0
		if conflict_files:
			summary_dict[project][f"Number of files merged for {project}"] = merge_files(conflict_files, project)

	print("--Summary--:")

	for project, summary_for_project in summary_dict.items():
		print(f"\n-Summary for platform: {project}")
		untracked_files = summary_for_project.pop(f"files without script {project}")
		pprint(summary_for_project)
		if summary_for_project[f"Number of files found for {project}"] != summary_for_project[f"Number of files moved for {project}"] + summary_for_project[f"Number of files merged for {project}"]:
			print("THE FOLLOWING FILES WERE NOT TAKEN CARE OF FOR ", project)
			for file in untracked_files:
				print(file)




