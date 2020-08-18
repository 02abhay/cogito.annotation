import json
import xmltodict


def main():
    with open("IMG_jeff@fruitscout.ai_1596729665.744972.xml") as xml_file:
        file_content = xml_file.read()
        data_dict = xmltodict.parse(file_content)
        xml_file.close()

        # creating variable to read data from xml
        var = data_dict['annotation']['object']

        # creating empty list to append all the values
        res = []

        # now make loop and append all the value in list
        for obj in var:
            b = obj['bndbox']
            # d is dictionay and have contain the other data in it
            d = dict(

                type='bbox',
                classId=12698,
                probability=100,

                # points is dictionary of dictionary inside list
                points=dict(
                x1=b['xmin'],
                x2=b['xmax'],
                y1=b['ymin'],
                y2=b['ymax']),

                groupId=0,
                pointLabels={},
                locked='false',
                visible='true',
                attributes=[],
                className='Mandarins',
            )
            # now append all the value in empty list
            res.append(d)

        #so, finally we are going to generate xml data to json format

        with open('data22.json', 'w') as f2:
            f2.write(json.dumps(res))
main()



