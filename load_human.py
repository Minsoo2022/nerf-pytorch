import os
import torch
import numpy as np
import imageio
import json
import torch.nn.functional as F
import cv2

trans_t = lambda t: torch.Tensor([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, t],
    [0, 0, 0, 1]]).float()

rot_phi = lambda phi: torch.Tensor([
    [1, 0, 0, 0],
    [0, np.cos(phi), -np.sin(phi), 0],
    [0, np.sin(phi), np.cos(phi), 0],
    [0, 0, 0, 1]]).float()

rot_theta = lambda th: torch.Tensor([
    [np.cos(th), 0, -np.sin(th), 0],
    [0, 1, 0, 0],
    [np.sin(th), 0, np.cos(th), 0],
    [0, 0, 0, 1]]).float()


def pose_spherical(theta, phi, radius):
    c2w = trans_t(radius)
    c2w = rot_phi(phi / 180. * np.pi) @ c2w
    c2w = rot_theta(theta / 180. * np.pi) @ c2w
    c2w = torch.Tensor(np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])) @ c2w
    return c2w


def load_human_data(basedir, half_res=False, testskip=1):

    all_imgs = []
    all_poses = []
    for i in range(360):
        i_str = str(i)
        fname = os.path.join(basedir, i_str.zfill(4) + '.jpg')
        fname_mask = fname.replace('color_re', 'mask_re').replace('jpg', 'png')
        mask = (imageio.imread(fname_mask)[None,] / 255.)[...,None]
        image = imageio.imread(fname)[None,]/ 255.
        all_imgs.append(np.concatenate((image,mask),axis=-1))
        pose = np.array(pose_spherical(i, 0, 10.0).cpu()[None,]) # pose = pose_spherical(i, 0, 10.0)
        all_poses.append(pose)

    # for s in splits:
    #     with open(os.path.join(basedir, 'transforms_{}.json'.format(s)), 'r') as fp:
    #         metas[s] = json.load(fp)

    # counts = [0]
    # for s in splits:
    #     meta = metas[s]
    #     imgs = []
    #     poses = []
    #     if s == 'train' or testskip == 0:
    #         skip = 1
    #     else:
    #         skip = testskip
    #
    #     for frame in meta['frames'][::skip]:
    #         fname = os.path.join(basedir, frame['file_path'] + '.png')
    #         imgs.append(imageio.imread(fname))
    #         poses.append(np.array(frame['transform_matrix']))
    #     imgs = (np.array(imgs) / 255.).astype(np.float32)  # keep all 4 channels (RGBA)
    #     poses = np.array(poses).astype(np.float32)
    #     counts.append(counts[-1] + imgs.shape[0])
    #     all_imgs.append(imgs)
    #     all_poses.append(poses)

    train_list = [a for a in list(range(360)) if a % 20 != 1 and a % 20 !=2]
    val_list = [a for a in list(range(360)) if a % 20 == 1]
    test_list = [a for a in list(range(360)) if a % 20 == 2]
    i_split = [train_list, val_list, test_list]

    imgs = np.concatenate(all_imgs, 0)
    poses = np.concatenate(all_poses, 0)

    H, W = imgs[0].shape[:2]
    focal = 5000

    render_poses = torch.stack([pose_spherical(angle, 0., 10.0) for angle in np.linspace(-180, 180, 40 + 1)[:-1]], 0)

    if half_res:
        H = H // 2
        W = W // 2
        focal = focal / 2.

        imgs_half_res = np.zeros((imgs.shape[0], H, W, 4))
        for i, img in enumerate(imgs):
            imgs_half_res[i] = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
        imgs = imgs_half_res
        # imgs = tf.image.resize_area(imgs, [400, 400]).numpy()

    return imgs, poses, render_poses, [H, W, focal], i_split

