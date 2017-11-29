import sdl2
import ctypes
from OpenGL import GL
from . import Vector4, Matrix4, GLWindow

class Scene(object):
    def __init__(self):
        self.objects = []
        self.hudObjects = []
        self.camera = Camera()
        self.camera.setPerspective()
        
        window = GLWindow.getInstance()
        self.center_x = window.size[0] // 2
        self.center_y = window.size[1] // 2
        
        sdl2.SDL_WarpMouseInWindow(window.window,
            ctypes.c_int(self.center_x), ctypes.c_int(self.center_y))
        sdl2.SDL_ShowCursor(0)
        
    def addObject(self, o):
        self.objects.append(o)
    
    def removeObject(self, o):
        self.objects.remove(o)
    
    def addHUDObject(self, o):
        self.hudObjects.append(o)
    
    def removeHUDObject(self, o):
        self.hudObjects.remove(o)
    
    def setCamera(self, camera):
        self.camera = camera
    
    def cleanup(self):
        for o in self.objects:
            o.cleanup()
    
    def update(self, dtime):
        keyState = sdl2.SDL_GetKeyboardState(None)
        if keyState[sdl2.SDL_SCANCODE_D]:
            self.camera.moveRight(dtime)
        if keyState[sdl2.SDL_SCANCODE_A]:
            self.camera.moveLeft(dtime)
        if keyState[sdl2.SDL_SCANCODE_W]:
            self.camera.moveForward(dtime)
        if keyState[sdl2.SDL_SCANCODE_S]:
            self.camera.moveBackward(dtime)
        if keyState[sdl2.SDL_SCANCODE_UP]:
            self.camera.rotate(dtime, ax=-1)
        if keyState[sdl2.SDL_SCANCODE_DOWN]:
            self.camera.rotate(dtime, ax=1)
        
        window = GLWindow.getInstance()
        
        x = ctypes.c_int()
        y = ctypes.c_int()
        mouseState = sdl2.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
        
        if x.value != 0 and y.value != 0:
        
            dx = self.center_x - x.value
            dy = self.center_y - y.value
            
            if dx > 0:
                self.camera.yaw(dtime, dx)
            elif dx < 0:
                self.camera.yaw(dtime, dx)
            
            if dy > 0:
                self.camera.rotate(dtime, ax=dy)
            elif dy < 0:
                self.camera.rotate(dtime, ax=dy)
            
            sdl2.SDL_WarpMouseInWindow(window.window,
                ctypes.c_int(self.center_x), ctypes.c_int(self.center_y))
        
        for o in self.objects:
            o.update(dtime)
        
        for o in self.hudObjects:
            o.update(dtime)
    
    def render(self):
        projMatrix = self.camera.getProjectionMatrix()
        projection_loc = GLWindow.getInstance().renderDelegate.projection_loc
        GL.glUniformMatrix4fv(projection_loc, 1, False, projMatrix.getCType())
        
        sampler_loc = GLWindow.getInstance().renderDelegate.sampler_loc
        GL.glUniform1i(sampler_loc, 0)
        
        camMatrix = self.camera.getViewMatrix()
        model_loc = GLWindow.getInstance().renderDelegate.model_loc
        modelview_loc = GLWindow.getInstance().renderDelegate.modelview_loc
        for o in self.objects:
            GL.glUniformMatrix4fv(model_loc, 1, False, o.modelMatrix.getCType())
            mvMatrix = camMatrix * o.modelMatrix
            GL.glUniformMatrix4fv(modelview_loc, 1, False, mvMatrix.getCType())
            o.render()
        
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        for o in self.hudObjects:
            GL.glUniformMatrix4fv(model_loc, 1, False, o.modelMatrix.getCType())
            mvMatrix = camMatrix * o.modelMatrix
            GL.glUniformMatrix4fv(modelview_loc, 1, False, mvMatrix.getCType())
            o.render()
        
        GL.glEnable(GL.GL_DEPTH_TEST)

class Camera(object):
    ORTHOGRAPHIC = 0
    PERSPECTIVE = 1
    
    def __init__(self):
        
        position = Vector4((0, 0.3, 0, 1))
        self.viewMatrix = Matrix4()
        self.viewMatrix.setPosition(position)
        
        self.translateSpeed = 5.0 / 5000.0
        self.rotateSpeed = 360.0 / 8000.0
        
        self.projection = Camera.ORTHOGRAPHIC
        self.projectionMatrix = Matrix4.getOrthographic(near=0.01, far=50)
        self.aspectRatio = 1.0
        self.target = None
        
        self.worldUp = Vector4((0, 1, 0, 0))
    
    def setPosition(self, position):
        self.viewMatrix.setPosition(position)
        if self.target:
            self.calculateOrientation()
    
    def setAspect(self, width, height):
        self.aspectRatio = float(width) / height
        if self.projection == Camera.ORTHOGRAPHIC:
            self.setOrthographic()
        elif self.projection == Camera.PERSPECTIVE:
            self.setPerspective()
    
    def getPosition(self):
        return self.viewMatrix.position()
    
    def getBasis(self):
        return self.viewMatrix.basis()
    
    def calculateOrientation(self):
        cameraPos = self.viewMatrix.position()
        lookat = (cameraPos - self.target).normalize()
        left = self.worldUp.cross(lookat).normalize()
        up = lookat.cross(left).normalize()
        
        self.viewMatrix.setOrientation(left, up, lookat)
        
    def getViewMatrix(self):
        return self.viewMatrix.inverse()
    
    def getProjectionMatrix(self):
        return self.projectionMatrix
    
    def setOrthographic(self):
        self.projection = Camera.ORTHOGRAPHIC
        self.projectionMatrix = Matrix4.getOrthographic(near=0.01, far=50,
            aspect=self.aspectRatio)
    
    def setPerspective(self):
        self.projection = Camera.PERSPECTIVE
        self.projectionMatrix = Matrix4.getPerspective(fovy=60, near=0.01,
            far=50, aspect=self.aspectRatio)
    
    def setTarget(self, target):
        self.target = target
        self.calculateOrientation()
    
    def yaw(self, dtime, direction):
        basis = self.getBasis()
        rotMatrix = Matrix4.getRotation(ay=direction*self.rotateSpeed * dtime)
        left = rotMatrix * basis[0]
        up = rotMatrix * basis[1]
        lookat = rotMatrix * basis[2]
        self.viewMatrix.setOrientation(left, up, lookat)
    
    def move(self, dtime, dx=0, dy=0, dz=0):
        dx *= self.translateSpeed * dtime
        dy *= self.translateSpeed * dtime
        dz *= self.translateSpeed * dtime
        self.viewMatrix = Matrix4.getTranslation(dx, dy, dz) * self.viewMatrix
    
    def rotate(self, dtime, ax=0, ay=0, az=0):
        ax *= self.rotateSpeed * dtime
        ay *= self.rotateSpeed * dtime
        az *= self.rotateSpeed * dtime
        self.viewMatrix *= Matrix4.getRotation(ax, ay, az)

    
    def rotateAboutTarget(self, dtime, ax=0, ay=0, az=0):
        if self.target:
            ax *= self.rotateSpeed * dtime
            ay *= self.rotateSpeed * dtime
            az *= self.rotateSpeed * dtime
            
            tranFromTarget = Matrix4.getTranslation(-self.target.getX(),
                                                    -self.target.getY(),
                                                    -self.target.getZ())
            self.viewMatrix = tranFromTarget * self.viewMatrix
            rotMatrix = Matrix4.getRotation(ax, ay, az)
            self.viewMatrix = rotMatrix * self.viewMatrix
            tranToTarget = Matrix4.getTranslation(self.target.getX(),
                                                  self.target.getY(),
                                                  self.target.getZ())
            
            self.viewMatrix = tranToTarget * self.viewMatrix
            self.calculateOrientation()
    
    def moveLeft(self, dtime):
        left = self.getBasis()[0]
        pos = self.getPosition()
        
        pos -= left * self.translateSpeed * dtime
        self.setPosition(pos)
    
    def moveRight(self, dtime):
        left = self.getBasis()[0]
        pos = self.getPosition()
        
        pos += left * self.translateSpeed * dtime
        self.setPosition(pos)
    
    def moveForward(self, dtime):
        lookat = self.getBasis()[2]
        pos = self.getPosition()
        
        pos -= lookat * self.translateSpeed * dtime
        self.setPosition(pos)
    
    def moveBackward(self, dtime):
        lookat = self.getBasis()[2]
        pos = self.getPosition()
        
        pos += lookat * self.translateSpeed * dtime
        self.setPosition(pos)