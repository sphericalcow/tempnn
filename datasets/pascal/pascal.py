import os 
import cv2
import cPickle
import matplotlib
import matplotlib.pyplot as plt
import xml.etree.ElementTree

PASCAL_PATH = '/home/omer/MyRoot/work/grideas/datasets/PASCAL/VOCdevkit/VOC2012/'

def parse_object(object_element, classnames=set(), poses=set()):
    classname = object_element.findtext('name')
    difficult = object_element.find('difficult')
    truncated = object_element.find('truncated')
    occluded = object_element.find('occluded')
    pose = object_element.find('pose')
    point = object_element.find('point')
    bndbox = object_element.find('bndbox')
        
    info = {'classname': classname,
            'difficult': difficult.text == '1' if difficult is not None else False,
            'truncated': truncated.text == '1' if truncated  is not None else False,
            'occluded': occluded.text == '1' if occluded  is not None else False,
            'pose': pose.text if pose is not None and pose.text.strip() != 'Unspecified' else None,
            'boundaries': ((float(bndbox.findtext('xmax')), float(bndbox.findtext('ymax'))),
                           (float(bndbox.findtext('xmin')), float(bndbox.findtext('ymin'))))} 
    
    actions = object_element.find('actions')
    if actions is not None:
        info['actions'] = [curr_action.tag for curr_action in actions.iter() if curr_action.text == '1']
    if point is not None:
        info['location'] = (float(point.findtext('x')), float(point.findtext('y'))),
    if info['pose'] is not None:
        poses.add(info['pose'])
    classnames.add(classname)
    return info, classnames, poses


def parse_xmls(relpath, base_path):
    images = {}
    classnames=set()
    poses=set()
    for root, dirs, files in os.walk(os.path.join(base_path, relpath)):
        for filename in files:
            fname, fext = os.path.splitext(filename)
            with open(os.path.join(root, filename), 'r') as f:
                element = xml.etree.ElementTree.fromstring(f.read())
            size_elemnent = element.find('size')
            objects = []
            for obj in element.findall('object'):
                obj_info, classnames, poses = parse_object(obj)
                objects.append(obj_info)
            curr_img = {'size': [int(size_elemnent.findtext('width')),
                                 int(size_elemnent.findtext('height')),
                                 int(size_elemnent.findtext('depth'))],
                        'segmented': element.findtext('segmented')=='1',
                        'objects': objects}
            images[fname] = curr_img
    return images, classnames, poses


def annotations(force=False, base_path=PASCAL_PATH):
    dmpfile = os.path.join(base_path, 'xmldumps.pkl')
    if force or not os.path.isfile(dmpfile):
        images, classnames, poses = parse_xmls('Annotations')
        with open(dmpfile, 'wb') as f:
            cPickle.dump((images, classnames, poses), f)        
    else:
        with open(dmpfile, 'rb') as f:
            images, classnames, poses = cPickle.load(f)
    return images, classnames, poses

def imagefile(imgname, base_path=PASCAL_PATH):
    return os.path.join(base_path, 'JPEGImages/'+imgname+'.jpg')

def segclassfile(imgname, base_path=PASCAL_PATH):
    return os.path.join(base_path, 'SegmentationClass/'+imgname+'.png')

def segobjectfile(imgname, base_path=PASCAL_PATH):
    return os.path.join(base_path, 'SegmentationObject/'+imgname+'.png')


# truncated, difficult, occluded
def showimg(images, imgname, base_path=PASCAL_PATH):
    def _show_main(axis):
        plt.suptitle(imgname + '(%d, %d, %d)'%(info['size'][0], info['size'][1], info['size'][2]))
        axis.imshow(image)
        axis.set_yticks([])
        axis.set_xticks([])
        axis.set_title('Localization')
        for obj in info['objects']:
            p1, p2 = obj['boundaries']
            axis.add_patch(matplotlib.patches.Rectangle(p1, p2[0]-p1[0], p2[1]-p1[1], alpha=0.25, facecolor="blue"))
            axis.text(p2[0], p2[1], obj['classname'], {'fontsize':14, 'weight' : 'bold', 'color':'red'})
            if obj['pose'] is not None:
                axis.text(p2[0], p2[1], obj['classname'] + '(%s)'%obj['pose'],
                          {'fontsize':14, 'weight' : 'bold', 'color':'red'})
            else:
                axis.text(p2[0], p2[1], obj['classname'], {'fontsize':14, 'weight' : 'bold', 'color':'red'})
    
    info = images[imgname]
    image = cv2.cvtColor(cv2.imread(imagefile(imgname, base_path)), cv2.COLOR_RGB2BGR)
    
    if info['segmented']:
        fig, ax = plt.subplots(1, 3)
        _show_main(ax[0])
        class_mask = cv2.cvtColor(cv2.imread(segclassfile(imgname, PASCAL_PATH)), cv2.COLOR_RGB2BGR)
        segments = image.copy()
        for c1 in xrange(class_mask.shape[2]):
            for c2 in xrange(class_mask.shape[2]):
                segments[class_mask[:, :, c1] != 0, c2] = 255
        ax[1].imshow(segments)
        ax[1].set_yticks([])
        ax[1].set_xticks([])
        ax[1].set_title('Segmentation: Classes')
        
        obj_mask = cv2.cvtColor(cv2.imread(segobjectfile(imgname, PASCAL_PATH)), cv2.COLOR_RGB2BGR)
        segments = image.copy()
        segments[obj_mask != 0]= obj_mask[obj_mask != 0]
        ax[2].imshow(segments)
        ax[2].set_yticks([])
        ax[2].set_xticks([])
        ax[2].set_title('Segmentation: Objects')
    else:
        fig, ax = plt.subplots(1, 1)
        _show_main(ax)

    plt.show()    
