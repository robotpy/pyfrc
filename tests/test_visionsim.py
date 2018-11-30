from math import radians as rad, pi

from pyfrc.physics.visionsim import VisionSimTarget


def test_visionsim_target1():

    # target is facing east, 90 degree viewing angle
    target = VisionSimTarget(0, 0, 315, 45)
    target.view_dst_start = 2
    target.view_dst_end = 4
    target.fov2 = rad(30)

    # check too close
    assert target.compute(0, 1, 1, 0) is None
    assert target.compute(0, -1, 1, 0) is None
    assert target.compute(0, 1, -1, 0) is None
    assert target.compute(0, -1, -1, 0) is None

    # check too far
    assert target.compute(0, 20, 20, 0) is None
    assert target.compute(0, -20, 20, 0) is None
    assert target.compute(0, 20, -20, 0) is None
    assert target.compute(0, -20, -20, 0) is None

    # check facing the right direction, outside of the view range
    assert target.compute(0, -2, -2, rad(-45)) is None
    assert target.compute(0, -2, 2, rad(45)) is None

    assert target.compute(0, 1, -2, rad(-135)) is None
    assert target.compute(0, 1, 2, rad(135)) is None

    # check facing the wrong direction, inside of the view range
    assert target.compute(0, 2, 2, rad(0)) is None
    assert target.compute(0, 2, -2, rad(0)) is None

    assert target.compute(0, 2, 2, rad(180)) is None
    assert target.compute(0, 2, -2, rad(180)) is None

    # check facing the right direction , inside of the view range
    result = target.compute(0, 2, 0, rad(180))
    assert result is not None
    assert result[0] == 1
    assert result[1] == 0
    assert result[2] == 0

    # TODO: add more tests here from different angles

    assert target.compute(0, 2, 2, rad(-135)) is not None
    assert target.compute(0, 2, -2, rad(135)) is not None

    assert target.compute(0, 2.07, -1.96, rad(140)) is not None
    # assert target.compute(0, 2, -2, rad(-135)) is not None


def test_visionsim_target2():

    # normalization function used by vision sim
    def _norm(angle):
        return ((rad(angle) + pi) % (pi * 2)) - pi

    # target is facing east, 90 degree viewing angle
    target = VisionSimTarget(18.5, 16, 315, 45)
    target.view_dst_start = 1.5
    target.view_dst_end = 15
    target.fov2 = rad(61.0 / 2.0)

    result = target.compute(0, 25, 16, _norm(-180))
    assert result is not None
    assert result[1] == 0

    result = target.compute(0, 25, 16, _norm(180))
    assert result is not None
    assert result[1] == 0

    # robot is northwest of target
    assert target.compute(0, 21.24, 13.82, _norm(206)) is None
    assert target.compute(0, 21.24, 13.82, _norm(149)) is not None
    assert target.compute(0, 21.24, 13.82, _norm(107)) is None
    assert target.compute(0, 21.24, 13.82, _norm(12.64)) is None
    assert target.compute(0, 21.24, 13.82, _norm(-136)) is None
    assert target.compute(0, 21.24, 13.82, _norm(-203)) is not None
    assert target.compute(0, 21.24, 13.82, _norm(943)) is None

    # robot is southwest of target
    assert target.compute(0, 20.22, 17.56, _norm(46)) is None
    assert target.compute(0, 20.22, 17.56, _norm(107)) is None
    assert target.compute(0, 20.22, 17.56, _norm(152.30)) is None
    assert target.compute(0, 20.22, 17.56, _norm(204.20)) is not None
    assert target.compute(0, 20.22, 17.56, _norm(-506.52)) is not None

    assert target.compute(0, 12.48, 13.79, _norm(24.61)) is None
