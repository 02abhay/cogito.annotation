import json

# input output json file

input_file = open('labelMe.json', 'r')
output_file = open('dataloop.json', 'w')
json_decode = json.load(input_file)
print(json_decode)
# iterating in input file
data = []

for item in json_decode.get('shapes'):
    # my_dict = {}
    #
    # my_dict['labels']=item.get('labels')
    # my_dict['description']=item.get('points')
    # my_dict['shape_type']=item.get('shape_type')
    # print(my_dict)

    data.append(item)
# creating output file
back_json = json.dumps(data)
output_file.write(back_json)
output_file.close()





