import math


class DrawableElement(object):
    '''
        Represents an object on the canvas that can move around and consist of multiple graphic elements.
    '''

    def __init__(self, canvas, start_position, scale=10):
        
        self.canvas = canvas
        self.scale = scale
        self.set_position(start_position)    # [x,y,r]
        self.canvas_elements = {}  # Dictionary of canvas elements to render

    def create_rectangle(self, top_left, bottom_right, color):
        vertices = [
            top_left,
            [top_left[0], bottom_right[1]],
            bottom_right,
            [bottom_right[0], top_left[1]],
        ]
        self.create_polygon(vertices, color)

    def create_polygon(self, vertices, color):
        canvas_coords = self._get_canvas_coords(vertices)
        polygon_id = self.canvas.create_polygon(*canvas_coords, fill=color)
        self.canvas_elements[polygon_id] = {
            "type": "polygon",
            "vertices": vertices,
            "color": color
        }
        return polygon_id

    def create_text(self, text, position, color, font_size):
        text_id = self.canvas.create_text(*position, text=text, font=("Helvetica", font_size, "bold"))
        self.canvas_elements[text_id] = {
            "type": "text",
            "text": text,
            "position": position,
            "font_size": font_size,
            "color": color
        }
        return text_id

    def set_position(self, new_position):
        self.position = new_position

    def _get_canvas_coords(self, vertices):
        canvas_coords = []
        for point in vertices:
            canvas_coords.extend(self._get_canvas_coord(point))
        return canvas_coords

    def _get_canvas_coord(self, point):
        x_in = point[0]*self.scale
        y_in = point[1]*self.scale
        x_out = self.position[0]*self.scale + (math.cos(self.position[2])*x_in - math.sin(self.position[2])*y_in)
        y_out = self.position[1]*self.scale + (math.sin(self.position[2])*x_in + math.cos(self.position[2])*y_in)
        return [x_out, y_out]
        
    def update_canvas(self):
        for element_id in self.canvas_elements:
            element = self.canvas_elements[element_id]
            if element["type"] == "polygon":
                canvas_coords = self._get_canvas_coords(element["vertices"])
                self.canvas.coords(element_id, canvas_coords)
                self.canvas.itemconfig(element_id, fill=element["color"])
            elif element["type"] == "text":
                self.canvas.coords(element_id, self._get_canvas_coord(element["position"]))
                self.canvas.itemconfig(element_id, fill=element["color"])


class RobotElement(DrawableElement):

    def __init__(self, canvas, controller, scale):

        # Load params from the user's sim/config.json
        self.controller = controller

        super().__init__(canvas, controller.get_position(), scale)

        # create a bunch of polygons that represent the robot
        config = controller.get_config()
        robot_w, robot_h = config.get('robot_dimensions', [2, 3])

        # Draw big robot rectangle
        self.robot_poly = self.create_polygon([
            (-robot_w/2, -robot_h/2),
            (robot_w/2, -robot_h/2),
            (robot_w/2, robot_h/2),
            (- robot_w/2, robot_h/2),
        ], 'red')

        # Draw robot arrow
        self.robot_arrow_poly = self.create_polygon([
            (-robot_w/2, -robot_h/2),
            (0, robot_h/2),
            (robot_w/2, -robot_h/2),
        ], 'green')

        # Draw wheels
        wheel_size = config.get("wheel_dimensions", [.3, .5])
        self.create_rectangle(
            [-robot_w/2 - wheel_size[0], robot_h/2],
            [-robot_w/2, robot_h/2 - wheel_size[1]],
            "black")
        self.create_rectangle(
            [robot_w/2, robot_h/2],
            [robot_w/2 + wheel_size[0], robot_h/2 - wheel_size[1]],
            "black")
        self.create_rectangle(
            [-robot_w/2 - wheel_size[0], -robot_h/2 + wheel_size[1]],
            [-robot_w/2, -robot_h/2],
            "black")
        self.create_rectangle(
            [robot_w/2, -robot_h/2 + wheel_size[1]],
            [robot_w/2 + wheel_size[0], -robot_h/2],
            "black")

    def update_canvas(self):
        self.set_position(self.controller.get_position())
        if not self.controller.is_alive():
            self.canvas_elements[self.robot_arrow_poly]["color"] = 'gray'
        super().update_canvas()
