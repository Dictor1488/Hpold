package inq.hpold.battle
{
   import flash.display.Bitmap;
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Shape;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.filters.DropShadowFilter;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;
   import inq.hpold.injector.BattleDisplayable;

   /**
    * Independent HP bars rendered with the original PlayersPanelHP textures.
    * The fill is clipped instead of stretched, preserving the source artwork.
    */
   public class PlayerPanelsUI extends BattleDisplayable
   {
      [Embed(source="../../../../../../vendor/res/gui/hpbars/hp_bg.png")]
      private static const HP_BG:Class;

      [Embed(source="../../../../../../vendor/res/gui/hpbars/hp_alive_l.png")]
      private static const HP_ALIVE_LEFT:Class;

      [Embed(source="../../../../../../vendor/res/gui/hpbars/hp_alive_r.png")]
      private static const HP_ALIVE_RIGHT:Class;

      [Embed(source="../../../../../../vendor/res/gui/hpbars/hp_alive_cb.png")]
      private static const HP_ALIVE_COLORBLIND:Class;

      private static const WIDTH:Number = 72;
      private static const HEIGHT:Number = 14;
      private var _rows:Dictionary = new Dictionary();
      private var _wanted:Dictionary = new Dictionary();
      private var _lastLayout:int = 0;

      public function PlayerPanelsUI()
      {
         super();
         addEventListener(Event.ENTER_FRAME, relayout);
      }

      public function as_create(linkage:String, kind:String, config:Object):void
      {
         // Retained for the DAAPI contract; rows are created by as_update.
      }

      public function as_update(linkage:String, data:Object):void
      {
         if (linkage != "hp_row" || data == null || !data.hasOwnProperty("vehicleID"))
            return;
         var id:int = int(data.vehicleID);
         var row:Sprite = _rows[id] as Sprite;
         if (row == null)
         {
            row = makeRow();
            _rows[id] = row;
         }
         _wanted[id] = Boolean(data.visible) && Number(data.maximum) > 0 &&
                       Number(data.current) > 0;
         row.visible = Boolean(_wanted[id]);
         var current:int = Math.max(0, int(data.current));
         var maximum:int = Math.max(1, int(data.maximum));
         var ratio:Number = Math.max(0, Math.min(1, Number(current) / maximum));
         var fillLayer:Sprite = row.getChildByName("fillLayer") as Sprite;
         var fillMask:Shape = row.getChildByName("fillMask") as Shape;
         var label:TextField = row.getChildByName("hpLabel") as TextField;
         var enemy:Boolean = placeRow(id, row);
         selectFill(fillLayer, enemy);
         fillLayer.visible = Boolean(data.showBar) && ratio > 0;
         fillMask.graphics.clear();
         fillMask.graphics.beginFill(0xFFFFFF);
         fillMask.graphics.drawRect(0, 0, Math.round(WIDTH * ratio), HEIGHT);
         fillMask.graphics.endFill();
         label.text = current + "/" + maximum;
      }

      public function as_delete(linkage:String):void
      {
         if (linkage != "hp_row")
            return;
         for (var id:* in _rows)
         {
            var row:Sprite = _rows[id] as Sprite;
            if (row && row.parent)
               row.parent.removeChild(row);
            delete _rows[id];
            delete _wanted[id];
         }
      }

      private function makeRow():Sprite
      {
         var row:Sprite = new Sprite();
         row.mouseEnabled = false;
         row.mouseChildren = false;

         var background:Bitmap = makeBitmap(HP_BG, "background");
         background.x = 1;
         background.y = 1;
         row.addChild(background);

         var fillLayer:Sprite = new Sprite();
         fillLayer.name = "fillLayer";
         fillLayer.addChild(makeBitmap(HP_ALIVE_LEFT, "ally"));
         fillLayer.addChild(makeBitmap(HP_ALIVE_RIGHT, "enemy"));
         fillLayer.addChild(makeBitmap(HP_ALIVE_COLORBLIND, "colorblind"));
         row.addChild(fillLayer);

         var fillMask:Shape = new Shape();
         fillMask.name = "fillMask";
         row.addChild(fillMask);
         fillLayer.mask = fillMask;

         var label:TextField = new TextField();
         label.name = "hpLabel";
         label.defaultTextFormat = new TextFormat("Arial", 11, 0xFFFFFF, true, null, null, null, null, "center");
         label.width = WIDTH;
         label.height = 18;
         label.x = 0;
         label.y = -2;
         label.selectable = false;
         label.mouseEnabled = false;
         label.wordWrap = false;
         label.filters = [new DropShadowFilter(1, 90, 0, 1, 2, 2, 2)];
         row.addChild(label);
         return row;
      }

      private function makeBitmap(asset:Class, name:String):Bitmap
      {
         var bitmap:Bitmap = new asset() as Bitmap;
         bitmap.name = name;
         bitmap.smoothing = false;
         return bitmap;
      }

      private function selectFill(layer:Sprite, enemy:Boolean):void
      {
         var ally:DisplayObject = layer.getChildByName("ally");
         var red:DisplayObject = layer.getChildByName("enemy");
         var colorblind:DisplayObject = layer.getChildByName("colorblind");
         ally.visible = !enemy;
         red.visible = enemy;
         colorblind.visible = false;
      }

      private function placeRow(vehicleID:int, row:Sprite):Boolean
      {
         try
         {
            if (battlePage == null)
               return false;
            var panel:* = battlePage["playersPanel"];
            if (panel == null)
               return false;
            var holder:* = panel.listLeft.getHolderByVehicleID(vehicleID);
            var enemy:Boolean = false;
            if (holder == null)
            {
               holder = panel.listRight.getHolderByVehicleID(vehicleID);
               enemy = true;
            }
            if (holder == null || holder._listItem == null)
            {
               row.visible = false;
               return enemy;
            }
            var item:DisplayObjectContainer = holder._listItem as DisplayObjectContainer;
            if (item == null || holder._listItem.vehicleIcon == null)
               return enemy;
            if (row.parent != item)
            {
               if (row.parent != null)
                  row.parent.removeChild(row);
               item.addChild(row);
            }
            var icon:DisplayObject = holder._listItem.vehicleIcon as DisplayObject;
            row.x = Math.round(icon.x + (enemy ? -176 : 85));
            row.y = Math.round(icon.y + 2);
            row.visible = Boolean(_wanted[vehicleID]);
            return enemy;
         }
         catch (e:Error)
         {
            trace("[inq_hpold] placeRow " + vehicleID + ": " + e.message);
            return false;
         }
         // Older ASC/Flex control-flow analysis does not treat try/catch as
         // exhaustive even though both branches above return a Boolean.
         return false;
      }

      private function relayout(event:Event):void
      {
         var now:int = getTimer();
         if (now - _lastLayout < 250)
            return;
         _lastLayout = now;
         for (var id:* in _rows)
         {
            var row:Sprite = _rows[id] as Sprite;
            if (row != null)
               placeRow(int(id), row);
         }
      }

      override protected function onDispose():void
      {
         removeEventListener(Event.ENTER_FRAME, relayout);
         as_delete("hp_row");
         super.onDispose();
      }
   }
}
