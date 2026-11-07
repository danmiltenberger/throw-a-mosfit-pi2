from tam_topdown import get_angle_of_object_deg_from_3oclock, get_dis_and_angle_deg_to_obj_from_two_cam

px_right = 499
px_left = 456

totaL_width = 1280


angle_left = round(get_angle_of_object_deg_from_3oclock(px_left),1)
angle_right = round(get_angle_of_object_deg_from_3oclock(px_right),1)


dis_from_center, angle_from_center = get_dis_and_angle_deg_to_obj_from_two_cam(angle_left, angle_right)

print(f"{round(angle_left,1)}deg left {round(angle_right,1)}deg right")

print(f"{round(dis_from_center)}in forward at {round(angle_from_center)}deg")
