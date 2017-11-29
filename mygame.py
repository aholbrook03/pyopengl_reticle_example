import ctypes
import sdl2
from math import *
import random
from OpenGL import GL
from etgg2801 import *

texture_phong_vsrc = b'''
#version 400

layout (location = 0) in vec3 VertexPosition;
layout (location = 1) in vec2 UV;
layout (location = 2) in vec3 VertexNormal;

out vec4 normal;
out vec2 texCoord;
out vec4 eyeVertex;
uniform mat4 modelview;
uniform mat4 model;
uniform mat4 projection;

void main()
{
    normal = normalize(model * vec4(VertexNormal, 0.0));
    texCoord = UV;
    eyeVertex = model * vec4(VertexPosition, 1.0);
    gl_Position = projection * modelview * vec4(VertexPosition, 1.0);
}
'''

texture_phong_fsrc = b'''
#version 400

in vec4 normal;
in vec2 texCoord;
in vec4 eyeVertex;
out vec4 FragColor;

uniform sampler2D sampler;

void main() {
    vec4 c = texture(sampler, texCoord).rgba;
    FragColor = clamp(c, 0.0, 1.0);
}
'''

class MyDelegate(GLWindowRenderDelegate):
    def __init__(self):
        super().__init__()
        
        self.initShaders()
        
        # location of model matrix in shader program
        self.modelview_loc = GL.glGetUniformLocation(self.shaderProgram, b"modelview")
        self.model_loc = GL.glGetUniformLocation(self.shaderProgram, b"model")
        self.projection_loc = GL.glGetUniformLocation(self.shaderProgram, b"projection")
        self.sampler_loc = GL.glGetUniformLocation(self.shaderProgram, b"sampler")
        
        # set background color to black
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        
        # enable face culling (backface by default)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        
        # (Rs Sr + Rd Dr, Gs Sg + Gd Dg, Bs Sb + Bd Db, As Sa + Ad Da)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        self.window = GLWindow.getInstance()
        GL.glViewport(0, 0, window.size[0], window.size[1])
        
        self.scene = Scene()
        self.scene.camera.setAspect(window.size[0], window.size[1])
        
    def initShaders(self):
        
        # build vertex shader object
        self.vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(self.vertexShader, texture_phong_vsrc)
        GL.glCompileShader(self.vertexShader)
        result = GL.glGetShaderiv(self.vertexShader, GL.GL_COMPILE_STATUS)
        if result != 1:
            print(GL.glGetShaderInfoLog(self.vertexShader))
            raise Exception("Error compiling vertex shader")
        
        # build fragment shader object
        self.fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(self.fragmentShader, texture_phong_fsrc)
        GL.glCompileShader(self.fragmentShader)
        result = GL.glGetShaderiv(self.fragmentShader, GL.GL_COMPILE_STATUS)
        if result != 1:
            print(GL.glGetShaderInfoLog(self.fragmentShader))
            raise Exception("Error compiling fragment shader")
        
        # build shader program and attach shader objects
        self.shaderProgram = GL.glCreateProgram()
        GL.glAttachShader(self.shaderProgram, self.vertexShader)
        GL.glAttachShader(self.shaderProgram, self.fragmentShader)
        GL.glLinkProgram(self.shaderProgram)
        
    def cleanup(self):
        self.scene.cleanup()
        GL.glDeleteShader(self.vertexShader)
        GL.glDeleteShader(self.fragmentShader)
        GL.glDeleteProgram(self.shaderProgram)
    
    def update(self, dtime):
        self.scene.update(dtime)
    
    def render(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        GL.glUseProgram(self.shaderProgram)
        
        self.scene.render()
        
        GL.glUseProgram(0)

window = GLWindow((1000, 400))
window.setRenderDelegate(MyDelegate())

dm = OBJReader.readFile('boat.obj')
dm.addDiffuseTexture('boat_diffuse.png')
dm.loadToVRAM()

dm.setPosition(Vector4((0, 0, -1, 1)))

plane = ModelPart()
plane.addVertices([-1, 0,   1,
                    1, 0,   1,
                    1, 0, -1,
                   -1, 0, -1])
plane.addUVS([0,0, 1,0, 1,1, 0,1])
plane.addIndices([0, 1, 2, 3, 0, 2])
plane.addUVIndices([0, 1, 2, 3, 0, 2])
planeModel = Model()
planeModel.addPart(plane)
planeModel.addDiffuseTexture('wood.png')
planeModel.loadToVRAM()
planeModel.setPosition(Vector4((0, 0, -1, 1)))

plane2 = ModelPart()
plane2.addVertices([-0.2,  0.2, -0.2,
                    -0.2, -0.2, -0.2,
                     0.2, -0.2, -0.2,
                     0.2,  0.2, -0.2])

plane2.addUVS([0,0, 0,1, 1,1, 1,0])
plane2.addIndices([0, 1, 2, 3, 0, 2])
plane2.addUVIndices([0, 1, 2, 3, 0, 2])
planeModel2 = HUDModel()
planeModel2.addPart(plane2)
planeModel2.addDiffuseTexture('reticle.png')
planeModel2.loadToVRAM()

window.renderDelegate.scene.addObject(dm)
window.renderDelegate.scene.addObject(planeModel)
window.renderDelegate.scene.addHUDObject(planeModel2)

window.mainLoop()