import argparse
import os
from collections import defaultdict
from collections import OrderedDict
from shutil import copy

import cv2
import xmltodict

ANNOTATION_EXTENTION = '.xml'
IMAGE_EXTENSION = '.jpg'


def load_annotation(folder, filename_without_extension):
    file = os.path.join(folder, filename_without_extension + '.xml')
    if os.path.isfile(file):
        with open(file) as file:
            ann = xmltodict.parse(file.read())
        ann = ann['annotation']
        # Invert the coordinates (labelImg has origin on hte left top corner and we want it on the left bottom one).
        h = int(ann['size']['height'])
        # If the annotation was done with labelImg, then this object is an OrderedDict or a list of OrderedDicts.
        if 'object' in ann:
            ann_object = ann['object']
            assert isinstance(ann_object, list) or isinstance(ann_object, OrderedDict)
            if isinstance(ann_object, OrderedDict):
                ann_object = [ann_object]
                ann['object'] = ann_object
            for obj in ann_object:
                y1 = int(obj['bndbox']['ymin'])
                y2 = int(obj['bndbox']['ymax'])
                x1 = int(obj['bndbox']['xmin'])
                x2 = int(obj['bndbox']['xmax'])
                x1, y1, x2, y2 = invert_image_coordinates(x1, y1, x2, y2, h)
                obj['bndbox']['xmin'] = str(x1)
                obj['bndbox']['ymin'] = str(y1)
                obj['bndbox']['xmax'] = str(x2)
                obj['bndbox']['ymax'] = str(y2)
            return ann
    else:
        print('No annotation found for this file: ', filename_without_extension)
        return None


def invert_image_coordinates(x1, y1, x2, y2, h):
    """ Image coordinates have origin on the top left corner and we want the origin to be on the bottom left corner. """
    return x1, h - y2, x2, h - y1


def check_image_without_xml(img_dir, xml_dir, validation_output_dir):
    """ Any files without annotation? """

    subdir = os.path.join(validation_output_dir, f'missing_xml')
    if not os.path.isdir(subdir):
        os.mkdir(subdir)

    rogue = []
    for file in os.listdir(img_dir):
        file_without_ext, ext = os.path.splitext(file)
        if ext != IMAGE_EXTENSION:
            continue
        xml_file = os.path.join(xml_dir, file_without_ext + ANNOTATION_EXTENTION)
        if not os.path.isfile(xml_file):
            rogue.append(file)

    for f in rogue:
        copy(os.path.join(img_dir, f), os.path.join(subdir, f))

    print(f'Number of images missing xml: {len(rogue)}')


def check_xml_without_image(img_dir, xml_dir, validation_output_dir):
    """ Any stray annotation lying around? """

    subdir = os.path.join(validation_output_dir, f'missing_image')
    if not os.path.isdir(subdir):
        os.mkdir(subdir)

    rogue = []
    for file in os.listdir(xml_dir):
        file_without_ext, ext = os.path.splitext(file)
        if ext != ANNOTATION_EXTENTION:
            continue
        image_file = os.path.join(img_dir, file_without_ext + IMAGE_EXTENSION)
        if not os.path.isfile(image_file):
            rogue.append(file)

    for f in rogue:
        copy(os.path.join(xml_dir, f), os.path.join(subdir, f))

    print(f'Number of xmls missing image: {len(rogue)}')


def check_xml_content(xml_dir, validation_output_dir):

    subdir = os.path.join(validation_output_dir, f'empty_annotation')
    if not os.path.isdir(subdir):
        os.mkdir(subdir)

    rogue = []
    for file in os.listdir(xml_dir):

        file_without_ext, ext = os.path.splitext(file)
        if ext != ANNOTATION_EXTENTION:
            continue

        ann = load_annotation(xml_dir, file_without_ext)
        if not ann:
            # Files with missing annotation will be handled by a different method.
            continue
        else:
            try:
                ann = ann['object']
            except Exception as e:
                print(e)
                print(f'Error loading annotation xml for file {file}')
                continue

            file_classes = set()
            for annotation_box in ann:
                file_classes.add(annotation_box['name'])

            if not file_classes:
                rogue.append(file)

    for f in rogue:
        copy(os.path.join(xml_dir, f), os.path.join(subdir, f))


def check_class_names(xml_dir, validation_output_dir, valid_classes):

    valid_classes = set(valid_classes + [v + 'Key' for v in valid_classes])

    subdir = os.path.join(validation_output_dir, f'invalid_class_names')
    if not os.path.isdir(subdir):
        os.mkdir(subdir)

    rogue = []
    for file in os.listdir(xml_dir):

        file_without_ext, ext = os.path.splitext(file)
        if ext != ANNOTATION_EXTENTION:
            continue

        ann = load_annotation(xml_dir, file_without_ext)
        if not ann:
            # Files with missing annotation will be handled by a different method.
            continue
        else:
            try:
                ann = ann['object']
            except Exception as e:
                print(e)
                print(f'Error loading annotation xml for file {file}')
                continue

            for annotation_box in ann:
                if annotation_box['name'] not in valid_classes:
                    rogue.append(file)
                    print('invalid class name: ', file, annotation_box['name'])

    for f in rogue:
        copy(os.path.join(xml_dir, f), os.path.join(subdir, f))


def check_xml_coordinates(img_dir, xml_dir, validation_output_dir):
    """ Any files without annotation? """

    subdir = os.path.join(validation_output_dir, f'invalid_coordinates')
    if not os.path.isdir(subdir):
        os.mkdir(subdir)

    rogue = []
    for file in os.listdir(img_dir):
        file_without_ext, ext = os.path.splitext(file)
        if ext != IMAGE_EXTENSION:
            continue
        xml_file = os.path.join(xml_dir, file_without_ext + ANNOTATION_EXTENTION)
        if not os.path.isfile(xml_file):
            continue

        ann = load_annotation(xml_dir, file_without_ext)
        if not ann:
            # Files with missing annotation will be handled by a different method.
            continue
        else:
            try:
                ann_w = int(ann['size']['width'])
                ann_h = int(ann['size']['height'])
                ann = ann['object']
            except Exception as e:
                print(e)
                print(f'Error loading annotation xml for file {file}')
                continue

            img = cv2.imread(os.path.join(img_dir, file))
            img_w = img.shape[1]
            img_h = img.shape[0]

            if abs(img_h - ann_h) / img_h > 0.05 or abs(img_w - ann_w) / img_w > 0.05:
                rogue.append(file)
                continue

            for annotation_box in ann:
                y1 = int(annotation_box['bndbox']['ymin'])
                y2 = int(annotation_box['bndbox']['ymax'])
                x1 = int(annotation_box['bndbox']['xmin'])
                x2 = int(annotation_box['bndbox']['xmax'])
                if x1 > img_w * 1.05 or x2 > img_w * 1.05 or y1 > img_h * 1.05 or y2 > img_h * 1.05:
                    rogue.append(file)
                    continue

    for f in rogue:
        copy(os.path.join(img_dir, f), os.path.join(subdir, f))

    print(f'Number of xml files with invalid coordinates: {len(rogue)}')


def check_missing_boxes(img_dir, xml_dir, validation_output_dir, classes_to_check):

    rogue = defaultdict(list)
    for file in os.listdir(xml_dir):

        file_without_ext, ext = os.path.splitext(file)
        if ext != ANNOTATION_EXTENTION:
            continue

        ann = load_annotation(xml_dir, file_without_ext)
        if not ann:
            # Files with missing annotation will be handled by a different method.
            continue
        else:
            try:
                ann = ann['object']
            except Exception as e:
                print(e)
                print(f'Error loading annotation xml for file {file}')
                continue

            file_classes = set()
            for annotation_box in ann:
                file_classes.add(annotation_box['name'])
            if not file_classes:
                # This was handled by a different method.
                continue

            for check_class in classes_to_check:
                if '|' not in check_class:
                    if check_class not in file_classes:
                        rogue[check_class].append(file_without_ext)
                else:
                    split_classes = check_class.split('|')
                    if all(check_split_class not in file_classes for check_split_class in split_classes):
                        if file_without_ext not in rogue[check_class]:
                            rogue[check_class].append(file_without_ext)

    for check_class in rogue:
        dir_c = os.path.join(validation_output_dir, f'missing_{check_class}')
        os.mkdir(dir_c)
        for file_without_ext in rogue[check_class]:
            copy(os.path.join(img_dir, file_without_ext + IMAGE_EXTENSION), os.path.join(dir_c, file_without_ext + IMAGE_EXTENSION))
            copy(os.path.join(xml_dir, file_without_ext + ANNOTATION_EXTENTION), os.path.join(dir_c, file_without_ext + ANNOTATION_EXTENTION))

    for check_class in classes_to_check:
        print(f"Number of files without class {check_class}: {len(rogue[check_class])}")


def check_more_than_n_boxes(img_dir, xml_dir, validation_output_dir, n_boxes, classes_to_check):

    rogue = defaultdict(list)
    for file in os.listdir(xml_dir):

        file_without_ext, ext = os.path.splitext(file)
        if ext != ANNOTATION_EXTENTION:
            continue

        ann = load_annotation(xml_dir, file_without_ext)
        if not ann:
            # Files with missing annotation will be handled by a different method.
            continue
        else:
            try:
                ann = ann['object']
            except Exception as e:
                print(e)
                print(f'Error loading annotation xml for file {file}')

            file_classes = list()
            for annotation_box in ann:
                file_classes.append(annotation_box['name'])
            if not file_classes:
                # This was handled by a different method.
                continue

            for check_class in classes_to_check:

                n_check_class = sum(1 for c in file_classes if c == check_class)

                if n_check_class > n_boxes:
                    rogue[check_class].append(file_without_ext)

    for check_class in rogue:
        dir_c = os.path.join(validation_output_dir, f'more_than_{n_boxes}_{check_class}')
        os.mkdir(dir_c)
        for file_without_ext in rogue[check_class]:
            copy(os.path.join(img_dir, file_without_ext + IMAGE_EXTENSION), os.path.join(dir_c, file_without_ext + IMAGE_EXTENSION))
            copy(os.path.join(xml_dir, file_without_ext + ANNOTATION_EXTENTION), os.path.join(dir_c, file_without_ext + ANNOTATION_EXTENTION))

    for check_class in classes_to_check:
        print(f"Number of files with more than {n_boxes} {check_class}: {len(rogue[check_class])}")


def check_key_classes(img_dir, xml_dir, validation_output_dir, classes_to_check):

    rogue = defaultdict(list)
    for file in os.listdir(xml_dir):

        file_without_ext, ext = os.path.splitext(file)
        if ext != ANNOTATION_EXTENTION:
            continue

        ann = load_annotation(xml_dir, file_without_ext)
        if not ann:
            # Files with missing annotation will be handled by a different method.
            continue
        else:
            try:
                ann = ann['object']
            except Exception as e:
                print(e)
                print(f'Error loading annotation xml for file {file}')

            file_classes = list()
            for annotation_box in ann:
                file_classes.append(annotation_box['name'])
            if not file_classes:
                # This was handled by a different method.
                continue

            for check_class in classes_to_check:

                n_check_class = sum(1 for c in file_classes if c == check_class)
                key_class = check_class + 'Key'
                n_key_class = sum(1 for c in file_classes if c == key_class)

                if n_check_class != n_key_class:
                    rogue[check_class].append(file_without_ext)

    for check_class in rogue:
        key_class = check_class + 'Key'
        dir_c = os.path.join(validation_output_dir, f'inconsistent_number_of_{key_class}')
        os.mkdir(dir_c)
        for file_without_ext in rogue[check_class]:
            copy(os.path.join(img_dir, file_without_ext + IMAGE_EXTENSION), os.path.join(dir_c, file_without_ext + IMAGE_EXTENSION))
            copy(os.path.join(xml_dir, file_without_ext + ANNOTATION_EXTENTION), os.path.join(dir_c, file_without_ext + ANNOTATION_EXTENTION))

    for check_class in classes_to_check:
        key_class = check_class + 'Key'
        print(f"Number of files with inconsistent number of {key_class}: {len(rogue[check_class])}")


def validate(img_dir, xml_dir, validation_output_dir):

    # Delete any old validation content and create a new folder.
    if os.path.isdir(validation_output_dir):
        print('The output directory already exists. Please delete the existing directory.')
        return
    else:
        os.mkdir(validation_output_dir)

    # Validate all other input directories.
    if not os.path.isdir(img_dir):
        print(f'Invalid directory: {img_dir}')
        return
    if not os.path.isdir(xml_dir):
        print(f'Invalid directory: {xml_dir}')
        return

    check_image_without_xml(img_dir=img_dir, xml_dir=xml_dir, validation_output_dir=validation_output_dir)
    check_xml_without_image(img_dir=img_dir, xml_dir=xml_dir, validation_output_dir=validation_output_dir)
    check_xml_content(xml_dir=xml_dir, validation_output_dir=validation_output_dir)
    check_xml_coordinates(img_dir=img_dir, xml_dir=xml_dir, validation_output_dir=validation_output_dir)

    check_class_names(xml_dir=xml_dir,
                      validation_output_dir=validation_output_dir,
                      valid_classes=['Shipper',
                                     'Consignee',
                                     'Carrier',
                                     'NotifyParty',
                                     'Issuer',
                                     'IssuerLogo',
                                     'DestinationAgent',
                                     'CompanyName',
                                     'Address',
                                     'FreightPaymentTerms',
                                     'ShippedOnBoardDate',
                                     'JobRef',
                                     'SCAC',
                                     'ExportRef'
                                     ])
    
    check_missing_boxes(img_dir=img_dir,
                        xml_dir=xml_dir,
                        validation_output_dir=validation_output_dir,
                        classes_to_check=['Shipper',
                                          'Consignee'
    ,                                     'Carrier',
                                          'NotifyParty',
                                          'Issuer',
                                          'IssuerLogo',
                                          'DestinationAgent',
                                          'CompanyName',
                                          'Address',
                                          'FreightPaymentTerms',
                                          'ShippedOnBoardDate',
                                          # 'JobRef',
                                          # 'SCAC',
                                          'ExportRef'
                                          ])
    check_more_than_n_boxes(img_dir=img_dir,
                            xml_dir=xml_dir,
                            validation_output_dir=validation_output_dir,
                            n_boxes=1,
                            classes_to_check=['Shipper',
                                              'Consignee',
                                              'Carrier',
                                              'NotifyParty',
                                              'Issuer',
                                              'IssuerLogo',
                                              'DestinationAgent',
                                              # 'CompanyName',
                                              # 'Address',
                                              'FreightPaymentTerms',
                                              'ShippedOnBoardDate',
                                              # 'JobRef',
                                              'SCAC',
                                              'ExportRef'
                                              ])
    check_key_classes(img_dir=img_dir,
                      xml_dir=xml_dir,
                      validation_output_dir=validation_output_dir,
                      classes_to_check=['Shipper',
                                        'Consignee',
                                        # 'Carrier',
                                        'NotifyParty',
                                        # 'Issuer',
                                        # 'IssuerLogo',
                                        'DestinationAgent',
                                        # 'CompanyName',
                                        # 'Address',
                                        # 'FreightPaymentTerms',
                                        'ShippedOnBoardDate',
                                        # 'JobRef',
                                        # 'SCAC',
                                        'ExportRef'
                                        ])


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--img_dir',
                        action='store',
                        help='The input image directory.',
                        default='/ANNOTATION/BOL/requirements/sample_bol_v1')
    parser.add_argument('--xml_dir',
                        action='store',
                        help='The input XML directory.',
                        required=False,
                        default='ANNOTATION/BOL/requirements/sample_bol_v1')
    parser.add_argument('--out_dir',
                        action='store',
                        help='The output directory.',
                        required=False,
                        default='/ANNOTATION/BOL/requirements/val')

    args = parser.parse_args()
    if args.img_dir and args.xml_dir and args.out_dir:
        validate(img_dir=args.img_dir,
                 xml_dir=args.xml_dir,
                 validation_output_dir=args.out_dir)


if __name__ == "__main__":
    main()
