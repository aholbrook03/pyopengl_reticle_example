# FILENAME: model.py
# BY: Andrew Holbrook
# DATE: 9/24/2015

import ctypes
from OpenGL import GL
from sdl2 import sdlimage
from . import GLWindow, Vector4, Matrix4

class Model(object):
    """Class for representing a Wavefront OBJ object.
    """
    def __init__(self):
        self.parts = []
        self.normals = []
        self.num_indices = 0
        self.textureObject = None
        self.modelMatrix = Matrix4()
    
    def __str__(self):
        return str(self.num_indices)
    
    def setPosition(self, pos):
        self.modelMatrix.setPosition(pos)
    
    def getNumParts(self):
        return len(self.parts)
    
    def getNumIndices(self):
        return self.num_indices
    
    def getNumNormals(self):
        return len(self.normals)
    
    def getOBJVertexList(self):
        objVertexList = []
        for p in self.parts:
            objVertexList += p.vertices
        
        return objVertexList
    
    def getOBJUVList(self):
        objUVList = []
        for p in self.parts:
            objUVList += p.uvs
        
        return objUVList
    
    def getVertexList(self):
        vertexList = []
        
        objVertList = self.getOBJVertexList()
        for i in self.getIndexList():
            vertexList += objVertList[i * 3 : i * 3 + 3]
        
        return vertexList
    
    def getUVList(self):
        uvList = []
        
        objUVList = self.getOBJUVList()
        for i in self.getUVIndexList():
            uvList += objUVList[i * 2 : i * 2 + 2]
        
        return uvList
    
    def getIndexList(self):
        tmpList = []
        for p in self.parts:
            tmpList += p.indices
        
        return tmpList
    
    def getUVIndexList(self):
        tmpList = []
        for p in self.parts:
            tmpList += p.uvIndices
        
        return tmpList
    
    def getNormalList(self):
        return self.normals
    
    def generateNormals(self):
        self.normals = []
        vertexList = self.getVertexList()
        for i in range(0, len(vertexList), 9):
            v0 = Vector4(vertexList[i : i + 3])
            v1 = Vector4(vertexList[i + 3 : i + 6])
            v2 = Vector4(vertexList[i + 6 : i + 9])
            
            n = (v1 - v0).cross(v2 - v1).normalize()
            self.normals += n.getXYZ() * 3
    
    def addPart(self, p):
        self.parts.append(p)
        self.num_indices += p.getNumIndices()
    
    def addDiffuseTexture(self, textureImage):
        GL.glActiveTexture(GL.GL_TEXTURE0)
        self.textureObject = GL.glGenTextures(1)
        
        surface = sdlimage.IMG_Load(bytes(textureImage, 'UTF-8'))
        pixels = ctypes.cast(surface.contents.pixels, ctypes.c_void_p)
        width = surface.contents.w
        height = surface.contents.h
        
        bmask = surface.contents.format.contents.Bmask
        
        imgFormat = GL.GL_RGBA
        if bmask == 255:
            imgFormat = GL.GL_BGRA
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureObject)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, width, height, 0,
            imgFormat, GL.GL_UNSIGNED_BYTE, pixels)
        
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    
    def cleanup(self):
        if self.textureObject != None:
            GL.glDeleteTextures(1, self.textureObject)
        GL.glDeleteBuffers(1, self.positionBuffer)
        GL.glDeleteVertexArrays(1, self.vertexArrayObject)
    
    def loadToVRAM(self):
        """Create the OpenGL objects for rendering this model.
        """
        
        # Create vertex array object to encapsulate the state needed to provide
        # vertex information.
        self.vertexArrayObject = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vertexArrayObject)
        
        # postition vertex buffer object
        self.positionBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.positionBuffer)
        
        # read and copy vertex data to VRAM
        vertexList = self.getVertexList()
        c_vertexArray = ctypes.c_float * len(vertexList)
        c_vertexArray = c_vertexArray(*vertexList)
        del vertexList
        
        GL.glBufferData(GL.GL_ARRAY_BUFFER, c_vertexArray, GL.GL_STATIC_DRAW)
        del c_vertexArray
        
        # position data is associated with location 0
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, 0, None)
        
        self.uvBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.uvBuffer)
        
        uvList = self.getUVList()
        uv = ctypes.c_float * len(uvList)
        uv = uv(*uvList)
        del uvList
        
        GL.glBufferData(GL.GL_ARRAY_BUFFER, uv, GL.GL_STATIC_DRAW)
        del uv
        
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, False, 0, None)
        
        self.generateNormals()
        
        self.normalBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.normalBuffer)
        
        c_normalArray = ctypes.c_float * len(self.normals)
        c_normalArray = c_normalArray(*self.normals)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, c_normalArray, GL.GL_STATIC_DRAW)
        del c_normalArray
        
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, False, 0, None)
        
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glEnableVertexAttribArray(2)
        
        GL.glBindVertexArray(0)
    
    def update(self, dtime):
        pass
    
    def render(self):
        self.renderAllParts()
    
    def renderPartByIndex(self, index):
        GL.glBindVertexArray(self.vertexArrayObject)
        
        if self.textureObject != None:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureObject)
        
        offset = 0
        for i in range(0, index):
            offset += self.parts[i].getNumIndices()
        
        c_offset = ctypes.c_void_p(offset * ctypes.sizeof(ctypes.c_uint))
        GL.glDrawElements(GL.GL_TRIANGLES, self.parts[index].getNumIndices(), GL.GL_UNSIGNED_INT, c_offset)
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glBindVertexArray(0)
        
    def renderPartByName(self, name):
        GL.glBindVertexArray(self.vertexArrayObject)
        
        if self.textureObject != None:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureObject)
        
        offset = 0
        for p in self.parts:
            if p.name == name:
                c_offset = ctypes.c_void_p(offset * ctypes.sizeof(ctypes.c_uint))
                GL.glDrawElements(GL.GL_TRIANGLES, p.getNumIndices(), GL.GL_UNSIGNED_INT, c_offset)
                break
            
            offset += p.getNumIndices()
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glBindVertexArray(0)
    
    def renderAllParts(self):
        GL.glBindVertexArray(self.vertexArrayObject)
        
        if self.textureObject != None:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureObject)
        
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.getNumIndices())
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        
        GL.glBindVertexArray(0)

class HUDModel(Model):
    def __init__(self):
        super().__init__()
    
    def update(self, dtime):
        super().update(dtime)
        
        camera = GLWindow.getInstance().renderDelegate.scene.camera
        
        x, y, z = camera.getBasis()
        p = camera.getPosition() - z * 1.0
        self.modelMatrix.setPosition(p)
        self.modelMatrix.setOrientation(x, y, z)
        

class ModelPart(object):
    """Represents a part (object) from the obj file.
    """
    def __init__(self):
        self.name = None
        self.vertices = []
        self.indices = []
        self.uvs = []
        self.uvIndices = []
    
    def getNumIndices(self):
        return len(self.indices)
    
    def getNumUVIndices(self):
        return len(self.uvIndices)
    
    def setName(self, name):
        self.name = name
    
    def addVertex(self, v):
        self.vertices.append(v)
    
    def addVertices(self, verts):
        self.vertices += verts
    
    def addIndex(self, i):
        self.indices.append(i)
    
    def addIndices(self, indices):
        self.indices += indices
    
    def addUV(self, uv):
        self.uvs.append(uv)
    
    def addUVS(self, uvs):
        self.uvs += uvs
    
    def addUVIndex(self, uvIndex):
        self.uvIndices.append(uvIndex)
    
    def addUVIndices(self, uvIndices):
        self.uvIndices += uvIndices

class OBJReader(object):
    
    @staticmethod
    def readFile(file):
        """Reads an .obj file and returns the data as a Model object.
        """
        model = Model()
        currentPart = None
        
        fp = open(file)
        
        for line in fp:
            if line[0:2] == 'v ':
                verts = line.split()
                for i in range(1, len(verts)):
                    currentPart.addVertex(float(verts[i]))
            elif line[0:2] == 'vt':
                uvs = line.split()
                for i in range(1, len(uvs)):
                    currentPart.addUV(float(uvs[i]))
            elif line[0] == 'f':
                indices = line.split()
                for i in range(1, len(indices)):
                    tmpIndex = indices[i].split('/')
                    currentPart.addIndex(int(tmpIndex[0]) - 1)
                    if len(tmpIndex) > 1:
                        currentPart.addUVIndex(int(tmpIndex[1]) - 1)
            elif line[0] == 'o':
                if currentPart == None:
                    currentPart = ModelPart()
                else:
                    model.addPart(currentPart)
                    currentPart = ModelPart()
                
                currentPart.setName(line.split()[1])
                
        fp.close()
        
        if currentPart != None:
            model.addPart(currentPart)
        
        return model